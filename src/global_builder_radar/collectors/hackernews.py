"""Hacker News monthly thread collectors.

Configuration:
- source.url points to the Algolia HN API base URL.
- options.thread_query controls the thread title search.
- `HackerNewsHiringCollector` reads the broad "Who is hiring?" thread and
  stays disabled until ordinary jobs can be separated reliably.
- `HackerNewsFreelancerCollector` reads the monthly "Freelancer? Seeking
  freelancer?" thread with source-specific semantics: only requester-side
  comments (`SEEKING FREELANCER` prefix) become opportunities; worker ads
  (`SEEKING WORK`) and chatter are rejected before persistence.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from html import unescape
from typing import Any

import httpx

from global_builder_radar.collectors.base import Collector, first_compensation, first_email
from global_builder_radar.models import CollectionResult, Opportunity, SourceConfig

TAG_PATTERN = re.compile(r"<[^>]+>")
_FREELANCER_THREAD_MARKER = "seeking freelancer"
_UNUSABLE_COMMENT = re.compile(r"(?i)^\s*\[(?:flagged|dead)]")


def _plain_html(value: str) -> str:
    return unescape(TAG_PATTERN.sub(" ", value)).replace("  ", " ").strip()


async def _find_thread(client: httpx.AsyncClient, base_url: str, query: str) -> str | None:
    """Return the newest thread id whose title contains the query, or None."""

    search = await client.get(
        f"{base_url}/search_by_date",
        params={"query": query, "tags": "story", "hitsPerPage": 20},
    )
    search.raise_for_status()
    hits = search.json().get("hits", [])
    exact = [hit for hit in hits if query.lower() in str(hit.get("title", "")).lower()]
    if not exact:
        return None
    thread = max(exact, key=lambda hit: str(hit.get("created_at", "")))
    return str(thread["objectID"])


class HackerNewsHiringCollector(Collector):
    async def collect(self) -> CollectionResult:
        started = time.perf_counter()
        query = str(self.source.options.get("thread_query", "Ask HN: Who is hiring?"))
        async with httpx.AsyncClient(timeout=self.source.timeout_seconds) as client:
            thread_id = await _find_thread(client, self.source.url, query)
            if thread_id is None:
                return CollectionResult(
                    source=self.source.id,
                    ok=False,
                    message="No current Who is Hiring thread found",
                    elapsed_seconds=time.perf_counter() - started,
                )
            tree_response = await client.get(f"{self.source.url}/items/{thread_id}")
            tree_response.raise_for_status()
            tree = tree_response.json()

        opportunities: list[Opportunity] = []
        for child in tree.get("children", []):
            raw_html = str(child.get("text") or "")
            description = _plain_html(raw_html)
            if not description:
                continue
            title = description.split("|")[0].strip()[:200] or f"HN hiring post {child['id']}"
            contact = first_email(description)
            opportunities.append(
                Opportunity(
                    source=self.source.id,
                    category=self.source.category,
                    external_id=str(child["id"]),
                    title=title,
                    description=description,
                    url=f"https://news.ycombinator.com/item?id={child['id']}",
                    contact_type="email" if contact else "hn_reply_or_link",
                    contact=contact,
                    compensation_text=first_compensation(description),
                    published_at=datetime.fromisoformat(
                        str(child["created_at"]).replace("Z", "+00:00")
                    )
                    if child.get("created_at")
                    else None,
                    remote="remote" in description.lower(),
                    tags=["hacker-news", "direct-company"],
                    raw_payload={"author": child.get("author"), "thread_id": thread_id},
                )
            )
            if len(opportunities) >= self.source.max_items:
                break
        return CollectionResult(
            source=self.source.id,
            opportunities=opportunities,
            elapsed_seconds=time.perf_counter() - started,
            message=f"thread={thread_id} accepted={len(opportunities)}",
        )


def allowed_comment_prefixes(source: SourceConfig) -> list[str]:
    """Return the normalized requester-side comment prefix allowlist."""

    configured = source.options.get("allowed_comment_prefixes")
    if isinstance(configured, list) and configured:
        return [str(prefix).strip().lower() for prefix in configured if str(prefix).strip()]
    return [_FREELANCER_THREAD_MARKER]


def comment_is_requester(text: str, prefixes: list[str]) -> bool:
    return any(text.lower().startswith(prefix) for prefix in prefixes)


def parse_freelancer_thread(
    tree: dict[str, Any], source: SourceConfig, elapsed_seconds: float
) -> CollectionResult:
    """Normalize a monthly freelancer thread into opportunities offline.

    Only top-level requester-side comments become opportunities; worker ads,
    flagged/dead comments, and chatter are rejected before persistence. A
    thread without requester comments is a truthful zero, not a failure.
    """

    thread_id = str(tree.get("id", ""))
    prefixes = allowed_comment_prefixes(source)
    opportunities: list[Opportunity] = []
    for child in tree.get("children", []):
        description = _plain_html(str(child.get("text") or ""))
        if not description or _UNUSABLE_COMMENT.match(description):
            continue
        if not comment_is_requester(description, prefixes):
            continue
        title = description.split("|")[0].strip()[:200] or f"HN requester post {child['id']}"
        contact = first_email(description)
        opportunities.append(
            Opportunity(
                source=source.id,
                category=source.category,
                external_id=str(child["id"]),
                title=title,
                description=description,
                url=f"https://news.ycombinator.com/item?id={child['id']}",
                contact_type="email" if contact else "hn_reply_or_link",
                contact=contact,
                compensation_text=first_compensation(description),
                published_at=datetime.fromisoformat(
                    str(child["created_at"]).replace("Z", "+00:00")
                )
                if child.get("created_at")
                else None,
                remote="remote" in description.lower(),
                tags=["hacker-news", "freelancer-thread"],
                raw_payload={"author": child.get("author"), "thread_id": thread_id},
            )
        )
        if len(opportunities) >= source.max_items:
            break
    return CollectionResult(
        source=source.id,
        opportunities=opportunities,
        elapsed_seconds=elapsed_seconds,
        message=f"thread={thread_id} parsed={len(tree.get('children', []))} "
        f"accepted={len(opportunities)}",
    )


class HackerNewsFreelancerCollector(Collector):
    async def collect(self) -> CollectionResult:
        started = time.perf_counter()
        query = str(self.source.options.get("thread_query", "Freelancer? Seeking freelancer?"))
        try:
            async with httpx.AsyncClient(timeout=self.source.timeout_seconds) as client:
                thread_id = await _find_thread(client, self.source.url, query)
                if thread_id is None:
                    return CollectionResult(
                        source=self.source.id,
                        ok=False,
                        message="No current freelancer/seeking-freelancer thread found",
                        elapsed_seconds=time.perf_counter() - started,
                    )
                tree_response = await client.get(f"{self.source.url}/items/{thread_id}")
                tree_response.raise_for_status()
                tree = tree_response.json()
        except httpx.HTTPError as exc:  # source isolation boundary
            return CollectionResult(
                source=self.source.id,
                ok=False,
                message=f"HN freelancer fetch failed: {type(exc).__name__}: {exc}",
                elapsed_seconds=time.perf_counter() - started,
            )
        return parse_freelancer_thread(tree, self.source, time.perf_counter() - started)
