"""Scrapling collector for public opportunity listing pages.

Configuration:
- options.fetcher: static, dynamic, or stealthy.
- options.link_pattern: substring required in opportunity links.
- No login, cookies, or private session data are used.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any
from urllib.parse import urljoin

from global_builder_radar.collectors.base import Collector, first_compensation
from global_builder_radar.models import CollectionResult, Opportunity, SourceConfig


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_listing_page(
    page: Any, source: SourceConfig, elapsed_seconds: float
) -> CollectionResult:
    """Normalize anchors from a fetched listing page into opportunities.

    Pure parsing: no network access, so sanitized HTML fixtures can test it.
    A page with zero matching links is reported as a failure because listing
    sources are expected to carry opportunities on every run.
    """

    link_pattern = str(source.options.get("link_pattern", ""))
    seen: set[str] = set()
    opportunities: list[Opportunity] = []
    for anchor in page.css("a[href]"):
        href = str(anchor.attrib.get("href", ""))
        if link_pattern and link_pattern not in href:
            continue
        url = urljoin(source.url, href)
        if url in seen:
            continue
        seen.add(url)
        context = _clean(anchor.get_all_text(separator=" ", strip=True))
        title_selector = str(source.options.get("title_selector", ""))
        title = ""
        if title_selector:
            title = _clean(str(anchor.css(title_selector).get() or ""))
        if not title:
            title = _clean(anchor.text or "")
        if not title:
            title = href.rstrip("/").split("/")[-1].replace("-", " ")
        opportunities.append(
            Opportunity(
                source=source.id,
                category=source.category,
                external_id=url,
                title=title[:500],
                description=context,
                url=url,
                contact_type="platform",
                compensation_text=first_compensation(context),
                remote=True,
                tags=[source.id, "public-listing"],
                raw_payload={"fetcher": source.options.get("fetcher", "static")},
            )
        )
        if len(opportunities) >= source.max_items:
            break
    ok = bool(opportunities)
    return CollectionResult(
        source=source.id,
        opportunities=opportunities,
        ok=ok,
        message=f"links_matched={len(opportunities)} pattern={link_pattern!r}",
        elapsed_seconds=elapsed_seconds,
    )


class ScraplingLinkCollector(Collector):
    async def collect(self) -> CollectionResult:
        started = time.perf_counter()
        try:
            page = await asyncio.to_thread(self._fetch)
        except Exception as exc:  # source isolation boundary
            return CollectionResult(
                source=self.source.id,
                ok=False,
                message=f"Scrapling fetch failed: {type(exc).__name__}: {exc}",
                elapsed_seconds=time.perf_counter() - started,
            )
        return parse_listing_page(page, self.source, time.perf_counter() - started)

    def _fetch(self):
        mode = str(self.source.options.get("fetcher", "static")).lower()
        if mode == "static":
            from scrapling.fetchers import Fetcher

            return Fetcher.get(self.source.url, timeout=self.source.timeout_seconds)
        if mode == "dynamic":
            from scrapling.fetchers import DynamicFetcher

            return DynamicFetcher.fetch(
                self.source.url,
                headless=True,
                network_idle=True,
                timeout=int(self.source.timeout_seconds * 1000),
            )
        if mode == "stealthy":
            from scrapling.fetchers import StealthyFetcher

            return StealthyFetcher.fetch(
                self.source.url,
                headless=True,
                network_idle=True,
                block_ads=True,
                timeout=int(self.source.timeout_seconds * 1000),
            )
        raise ValueError(f"Unsupported Scrapling fetcher: {mode}")
