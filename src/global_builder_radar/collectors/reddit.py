"""Reddit RSS collector.

Configuration:
- source.url points to a public Atom/RSS feed.
- options.required_flair_prefix defaults to [Hiring].
"""

from __future__ import annotations

import asyncio
import re
import time
from datetime import UTC, datetime
from html import unescape

import feedparser
import httpx
from dateutil import parser as date_parser

from global_builder_radar.collectors.base import Collector, first_compensation, first_email
from global_builder_radar.models import CollectionResult, Opportunity


class RedditRssCollector(Collector):
    async def collect(self) -> CollectionResult:
        started = time.perf_counter()
        headers = {"User-Agent": "GlobalBuilderRadar/0.1 (+https://growthtech.solutions)"}
        async with httpx.AsyncClient(
            timeout=self.source.timeout_seconds, headers=headers
        ) as client:
            response = await client.get(self.source.url, follow_redirects=True)
            response.raise_for_status()
        feed = await asyncio.to_thread(feedparser.parse, response.content)
        required_prefix = str(self.source.options.get("required_flair_prefix", "[Hiring]")).lower()
        opportunities: list[Opportunity] = []
        for entry in feed.entries:
            title = unescape(str(entry.get("title", ""))).strip()
            if required_prefix and not title.lower().startswith(required_prefix):
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
                    source=self.source.id,
                    category=self.source.category,
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
            if len(opportunities) >= self.source.max_items:
                break
        return CollectionResult(
            source=self.source.id,
            opportunities=opportunities,
            elapsed_seconds=time.perf_counter() - started,
            message=f"parsed={len(feed.entries)} accepted={len(opportunities)}",
        )
