"""GitHub issue search collector for public bounty signals.

Configuration:
- GITHUB_TOKEN is optional but raises GitHub API rate limits.
- options.query contains the GitHub issue search expression.
"""

from __future__ import annotations

import os
import time
from datetime import datetime

import httpx

from global_builder_radar.collectors.base import Collector, first_compensation
from global_builder_radar.models import CollectionResult, Opportunity, OpportunityStatus


class GitHubBountySearchCollector(Collector):
    async def collect(self) -> CollectionResult:
        started = time.perf_counter()
        query = str(self.source.options.get("query", "is:issue is:open label:bounty"))
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "global-builder-radar",
        }
        if token := os.getenv("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(
            timeout=self.source.timeout_seconds, headers=headers
        ) as client:
            response = await client.get(
                self.source.url,
                params={"q": query, "sort": "created", "order": "desc", "per_page": 100},
            )
            response.raise_for_status()
            payload = response.json()

        opportunities: list[Opportunity] = []
        marker = str(self.source.options.get("platform_marker", "")).lower()
        max_signal_repetitions = int(
            self.source.options.get("max_signal_repetitions", 25)
        )
        for item in payload.get("items", []):
            title = str(item.get("title") or "GitHub bounty")
            body = str(item.get("body") or "")
            labels = [str(label.get("name", "")) for label in item.get("labels", [])]
            evidence = " ".join([title, body, *labels]).lower()
            if marker and marker not in evidence:
                continue
            signal_repetitions = evidence.count("bounty") + evidence.count("reward")
            status = (
                OpportunityStatus.DISCARDED
                if signal_repetitions > max_signal_repetitions
                else OpportunityStatus.NEW
            )
            compensation = first_compensation(evidence)
            opportunities.append(
                Opportunity(
                    source=self.source.id,
                    category=self.source.category,
                    external_id=str(item.get("id")),
                    title=title,
                    description=body,
                    url=str(item.get("html_url")),
                    contact_type="github_issue",
                    compensation_text=compensation,
                    published_at=datetime.fromisoformat(
                        str(item["created_at"]).replace("Z", "+00:00")
                    )
                    if item.get("created_at")
                    else None,
                    remote=True,
                    tags=["github", "open-source", *labels],
                    raw_payload={
                        "repository_url": item.get("repository_url"),
                        "comments": item.get("comments"),
                        "platform_marker": marker,
                        "signal_repetitions": signal_repetitions,
                    },
                    status=status,
                )
            )
            if len(opportunities) >= self.source.max_items:
                break
        discarded_count = sum(
            item.status == OpportunityStatus.DISCARDED for item in opportunities
        )
        return CollectionResult(
            source=self.source.id,
            opportunities=opportunities,
            ok=bool(opportunities),
            elapsed_seconds=time.perf_counter() - started,
            message=(
                f"api_total={payload.get('total_count', 0)} "
                f"marker_matched={len(opportunities)} "
                f"discarded={discarded_count}"
            ),
        )
