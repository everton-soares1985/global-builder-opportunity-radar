"""Collection pipeline orchestration.

Configuration:
- Sources run concurrently and fail independently.
- Concurrency is intentionally bounded by the number of configured sources.
"""

from __future__ import annotations

import asyncio
import logging

from global_builder_radar.classification import classify_opportunity_kind
from global_builder_radar.config import ProfileRules
from global_builder_radar.extraction import enrich_opportunity
from global_builder_radar.models import CollectionResult, SourceConfig
from global_builder_radar.registry import build_collector
from global_builder_radar.scoring import score_opportunity
from global_builder_radar.storage import RadarStore

LOGGER = logging.getLogger(__name__)


async def _safe_collect(source: SourceConfig) -> CollectionResult:
    try:
        return await build_collector(source).collect()
    except Exception as exc:  # source isolation boundary
        LOGGER.exception("source_collection_failed source=%s", source.id)
        return CollectionResult(
            source=source.id,
            ok=False,
            message=f"{type(exc).__name__}: {exc}",
        )


async def run_collection(
    sources: list[SourceConfig], rules: ProfileRules, store: RadarStore
) -> list[CollectionResult]:
    results = await asyncio.gather(*(_safe_collect(source) for source in sources))
    for result in results:
        for opportunity in result.opportunities:
            opportunity.category = classify_opportunity_kind(opportunity)
            enrich_opportunity(opportunity)
            opportunity.score = score_opportunity(opportunity, rules)
        inserted, updated = store.record_result(result)
        LOGGER.info(
            "source_collection_complete source=%s ok=%s items=%s "
            "inserted=%s updated=%s elapsed=%.2f",
            result.source,
            result.ok,
            len(result.opportunities),
            inserted,
            updated,
            result.elapsed_seconds,
        )
    return results
