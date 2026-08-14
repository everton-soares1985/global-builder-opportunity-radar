"""Reddit RSS collector.

Configuration:
- source.url points to a public Atom/RSS feed.
- options.allowed_title_prefixes is a requester-side title allowlist
  (case-insensitive); options.required_flair_prefix remains as the legacy
  single-prefix form defaulting to [Hiring].
- Worker advertisements and chatter are rejected before persistence by the
  allowlist; ordinary employment that slips through is quarantined by the
  pipeline's opportunity-kind classification.
"""

from __future__ import annotations

import asyncio
import re
import time
from datetime import UTC, datetime
from html import unescape
from typing import Any

import feedparser
import httpx
from dateutil import parser as date_parser

from global_builder_radar.collectors.base import Collector, first_compensation, first_email
from global_builder_radar.models import CollectionResult, Opportunity, SourceConfig


def allowed_title_prefixes(source: SourceConfig) -> list[str]:
    """Return the normalized requester-side title prefix allowlist."""

    configured = source.options.get("allowed_title_prefixes")
    if isinstance(configured, list) and configured:
        return [str(prefix).strip().lower() for prefix in configured if str(prefix).strip()]
    legacy = str(source.options.get("required_flair_prefix", "[Hiring]")).strip()
    return [legacy.lower()] if legacy else []


def title_is_requester(title: str, prefixes: list[str]) -> bool:
    return any(title.lower().startswith(prefix) for prefix in prefixes)


def feed_is_unusable(feed: Any) -> tuple[bool, str]:
    """Distinguish a malformed or blocked feed from a legitimately empty one.

    Returns a (unusable, reason) pair. A bozo feed with no entries is
    malformed; a feed with no channel metadata (title or link) is a
    non-feed body such as an HTML block page, which feedparser accepts
    with bozo=0.
    """

    if getattr(feed, "bozo", 0) and not feed.entries:
        return True, "malformed_feed_body"
    info = feed.feed or {}
    if not feed.entries and not info.get("title") and not info.get("link"):
        return True, "non_feed_body"
    return False, ""


def parse_reddit_feed(feed: Any, source: SourceConfig, elapsed_seconds: float) -> CollectionResult:
    """Normalize feed entries into opportunities without network access."""

    unusable, reason = feed_is_unusable(feed)
    if unusable:
        return CollectionResult(
            source=source.id,
            ok=False,
            message=f"feed_parse_failed ({reason})",
            elapsed_seconds=elapsed_seconds,
        )
    prefixes = allowed_title_prefixes(source)
    opportunities: list[Opportunity] = []
    for entry in feed.entries:
        title = unescape(str(entry.get("title", ""))).strip()
        if prefixes and not title_is_requester(title, prefixes):
            continue
        body_html = unescape(str(entry.get("content", [{}])[0].get("value", "")))
        body = re.sub(r"<[^>]+>", " ", body_html)
        body = re.sub(r"\s+", " ", body).strip()
        published_at = None
        if published := entry.get("published"):
            parsed = date_parser.parse(str(published))
            published_at = parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        contact = first_email(body)
        opportunities.append(
            Opportunity(
                source=source.id,
                category=source.category,
                external_id=str(entry.get("id") or entry.get("link")),
                title=title,
                description=body,
                url=str(entry.get("link")),
                contact_type="email" if contact else "reddit_dm",
                contact=contact,
                compensation_text=first_compensation(f"{title} {body}"),
                published_at=published_at,
                remote=True,
                tags=["reddit", "direct-contact"],
                raw_payload={"author": entry.get("author")},
                collected_at=datetime.now(UTC),
            )
        )
        if len(opportunities) >= source.max_items:
            break
    return CollectionResult(
        source=source.id,
        opportunities=opportunities,
        elapsed_seconds=elapsed_seconds,
        message=f"parsed={len(feed.entries)} accepted={len(opportunities)}",
    )


class RedditRssCollector(Collector):
    async def collect(self) -> CollectionResult:
        started = time.perf_counter()
        headers = {"User-Agent": "GlobalBuilderRadar/0.1 (+https://growthtech.solutions)"}
        try:
            async with httpx.AsyncClient(
                timeout=self.source.timeout_seconds, headers=headers
            ) as client:
                response = await client.get(self.source.url, follow_redirects=True)
                response.raise_for_status()
        except httpx.HTTPError as exc:  # source isolation boundary
            return CollectionResult(
                source=self.source.id,
                ok=False,
                message=f"Reddit fetch failed: {type(exc).__name__}: {exc}",
                elapsed_seconds=time.perf_counter() - started,
            )
        feed = await asyncio.to_thread(feedparser.parse, response.content)
        return parse_reddit_feed(feed, self.source, time.perf_counter() - started)
