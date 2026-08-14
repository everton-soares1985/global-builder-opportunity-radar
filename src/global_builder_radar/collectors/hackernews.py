"""Hacker News monthly Who is Hiring collector.

Configuration:
- source.url points to the Algolia HN API base URL.
- options.thread_query controls the thread title search.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from html import unescape

import httpx

from global_builder_radar.collectors.base import Collector, first_compensation, first_email
from global_builder_radar.models import CollectionResult, Opportunity

TAG_PATTERN = re.compile(r"<[^>]+>")


def _plain_html(value: str) -> str:
    return unescape(TAG_PATTERN.sub(" ", value)).replace("  ", " ").strip()


class HackerNewsHiringCollector(Collector):
    async def collect(self) -> CollectionResult:
        started = time.perf_counter()
        query = str(self.source.options.get("thread_query", "Ask HN: Who is hiring?"))
        async with httpx.AsyncClient(timeout=self.source.timeout_seconds) as client:
            search = await client.get(
                f"{self.source.url}/search_by_date",
                params={"query": query, "tags": "story", "hitsPerPage": 20},
            )
            search.raise_for_status()
            hits = search.json().get("hits", [])
            exact = [hit for hit in hits if query.lower() in str(hit.get("title", "")).lower()]
            if not exact:
                return CollectionResult(
                    source=self.source.id,
                    ok=False,
                    message="No current Who is Hiring thread found",
                    elapsed_seconds=time.perf_counter() - started,
                )
            thread = max(exact, key=lambda hit: str(hit.get("created_at", "")))
            thread_id = str(thread["objectID"])
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
