"""Optional generic Apify Actor collector.

Configuration:
- APIFY_TOKEN is required.
- options.actor_id and options.actor_input define the Actor run.
- This adapter is disabled until a source explicitly selects it.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

from global_builder_radar.collectors.base import Collector, first_compensation, first_email
from global_builder_radar.models import CollectionResult, Opportunity


class ApifyActorCollector(Collector):
    async def collect(self) -> CollectionResult:
        started = time.perf_counter()
        apify_credential = os.getenv("APIFY_TOKEN")
        if not apify_credential:
            return CollectionResult(
                source=self.source.id,
                ok=False,
                message="APIFY_TOKEN is not configured",
                elapsed_seconds=time.perf_counter() - started,
            )
        try:
            items = await asyncio.to_thread(self._run_actor, apify_credential)
        except ImportError:
            return CollectionResult(
                source=self.source.id,
                ok=False,
                message="Install the project with the 'apify' extra",
                elapsed_seconds=time.perf_counter() - started,
            )
        opportunities: list[Opportunity] = []
        for index, item in enumerate(items):
            title = str(item.get("title") or item.get("name") or f"Apify result {index + 1}")
            description = str(item.get("description") or item.get("text") or "")
            url = str(item.get("url") or item.get("link") or self.source.url)
            contact = first_email(description)
            opportunities.append(
                Opportunity(
                    source=self.source.id,
                    category=self.source.category,
                    external_id=str(item.get("id") or url),
                    title=title,
                    description=description,
                    url=url,
                    contact_type="email" if contact else "platform",
                    contact=contact,
                    compensation_text=first_compensation(f"{title} {description}"),
                    raw_payload=item,
                )
            )
        return CollectionResult(
            source=self.source.id,
            opportunities=opportunities[: self.source.max_items],
            elapsed_seconds=time.perf_counter() - started,
            message=f"actor_items={len(items)}",
        )

    def _run_actor(self, apify_credential: str) -> list[dict[str, Any]]:
        from apify_client import ApifyClient

        actor_id = str(self.source.options["actor_id"])
        actor_input = dict(self.source.options.get("actor_input", {}))
        client = ApifyClient(apify_credential)
        run = client.actor(actor_id).call(run_input=actor_input)
        if not run:
            return []
        return list(client.dataset(run["defaultDatasetId"]).iterate_items())
