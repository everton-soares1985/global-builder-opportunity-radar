"""Opire public Next.js data collector.

Configuration:
- source.url points to the public Opire home page.
- The collector extracts the server-provided `initialRewards` payload.
- No login, session cookie, or private endpoint is used.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import UTC, datetime
from typing import Any

from global_builder_radar.collectors.base import Collector
from global_builder_radar.models import CollectionResult, Opportunity

NEXT_PUSH_PREFIX = "self.__next_f.push("
INITIAL_REWARDS_MARKER = '"initialRewards":'

# Titles often state the real reward ("... ($50)") while pendingPrice can be
# an aggregate; when both exist and disagree, the title evidence wins.
_TITLE_AMOUNT = re.compile(r"(?i)(?:US\$|\$)\s*(\d[\d,.]*)")


def parse_initial_rewards(script_texts: list[str]) -> list[dict[str, Any]]:
    for script_text in script_texts:
        if INITIAL_REWARDS_MARKER not in script_text and "initialRewards" not in script_text:
            continue
        if not script_text.startswith(NEXT_PUSH_PREFIX):
            continue
        outer_json = script_text.removeprefix(NEXT_PUSH_PREFIX).removesuffix(")")
        try:
            flight_chunk = json.loads(outer_json)
        except json.JSONDecodeError:
            continue
        if not isinstance(flight_chunk, list) or len(flight_chunk) < 2:
            continue
        payload = flight_chunk[1]
        if not isinstance(payload, str) or INITIAL_REWARDS_MARKER not in payload:
            continue
        start = payload.index(INITIAL_REWARDS_MARKER) + len(INITIAL_REWARDS_MARKER)
        try:
            rewards, _ = json.JSONDecoder().raw_decode(payload[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(rewards, list):
            return [reward for reward in rewards if isinstance(reward, dict)]
    return []


def resolve_reward_amount(reward: dict[str, Any]) -> str | None:
    """Return the compensation text for an Opire reward.

    Prefers an explicit amount stated in the issue title when the API
    pendingPrice disagrees with it, keeping the evidence plausibly
    individual instead of claiming an aggregate figure as pay.
    """

    title = str(reward.get("title") or "")
    title_amount = _TITLE_AMOUNT.search(title)
    price = reward.get("pendingPrice") or {}
    value = price.get("value")
    unit = str(price.get("unit") or "")
    pending = None
    if isinstance(value, (int, float)) and unit == "USD_CENT":
        pending = value / 100
    if title_amount:
        amount = float(title_amount.group(1).replace(",", ""))
        if pending is None or abs(pending - amount) > 0.01:
            return f"USD {amount:,.2f}"
    if pending is not None:
        return f"USD {pending:,.2f}"
    return None


class OpireNextDataCollector(Collector):
    async def collect(self) -> CollectionResult:
        started = time.perf_counter()
        try:
            page = await asyncio.to_thread(self._fetch)
        except Exception as exc:  # source isolation boundary
            return CollectionResult(
                source=self.source.id,
                ok=False,
                message=f"Opire fetch failed: {type(exc).__name__}: {exc}",
                elapsed_seconds=time.perf_counter() - started,
            )
        rewards = parse_initial_rewards([str(script.text or "") for script in page.css("script")])
        opportunities: list[Opportunity] = []
        for reward in rewards[: self.source.max_items]:
            compensation = resolve_reward_amount(reward)
            organization = reward.get("organization") or {}
            project = reward.get("project") or {}
            languages = [
                str(language)
                for language in reward.get("programmingLanguages", [])
                if language
            ]
            created_at = None
            if isinstance(reward.get("createdAt"), (int, float)):
                created_at = datetime.fromtimestamp(reward["createdAt"] / 1000, tz=UTC)
            opportunities.append(
                Opportunity(
                    source=self.source.id,
                    category=self.source.category,
                    external_id=str(reward.get("id") or reward.get("url")),
                    title=str(reward.get("title") or "Opire bounty"),
                    description=(
                        f"{organization.get('name', '')}/{project.get('name', '')} "
                        f"{', '.join(languages)}"
                    ).strip(),
                    url=str(reward.get("url")),
                    contact_type="github_issue",
                    compensation_text=compensation,
                    published_at=created_at,
                    remote=True,
                    tags=["opire", "open-source", *languages],
                    raw_payload={
                        "platform": reward.get("platform"),
                        "organization": organization.get("name"),
                        "project": project.get("name"),
                        "solver_count": len(reward.get("claimerUsers", [])),
                        "trying_count": len(reward.get("tryingUsers", [])),
                    },
                )
            )
        return CollectionResult(
            source=self.source.id,
            opportunities=opportunities,
            ok=bool(opportunities),
            message=f"initial_rewards={len(rewards)} accepted={len(opportunities)}",
            elapsed_seconds=time.perf_counter() - started,
        )
    def _fetch(self):
        from scrapling.fetchers import DynamicFetcher

        return DynamicFetcher.fetch(
            self.source.url,
            headless=True,
            network_idle=True,
            timeout=int(self.source.timeout_seconds * 1000),
        )
