import asyncio
import json
from pathlib import Path

from global_builder_radar import registry
from global_builder_radar.collectors.base import Collector
from global_builder_radar.config import ProfileRules
from global_builder_radar.models import (
    CollectionResult,
    Opportunity,
    OpportunityCategory,
    SourceConfig,
)
from global_builder_radar.pipeline import run_collection
from global_builder_radar.storage import RadarStore


class _MixedSourceCollector(Collector):
    async def collect(self) -> CollectionResult:
        job = Opportunity(
            source=self.source.id,
            category=self.source.category,
            external_id="job",
            title="Senior Engineer (full-time, benefits package)",
            description="Permanent employment with 401k and visa sponsorship.",
            url="https://example.com/job",
        )
        contract = Opportunity(
            source=self.source.id,
            category=self.source.category,
            external_id="contract",
            title="Contract automation developer",
            description="Fixed-term contractor engagement, project-based.",
            url="https://example.com/contract",
        )
        return CollectionResult(source=self.source.id, opportunities=[job, contract])


class _BrokenCollector(Collector):
    async def collect(self) -> CollectionResult:
        raise RuntimeError("simulated failure")


def test_pipeline_classifies_and_isolates_failures(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setitem(registry.COLLECTORS, "fake_mixed", _MixedSourceCollector)
    monkeypatch.setitem(registry.COLLECTORS, "fake_broken", _BrokenCollector)
    mixed_source = SourceConfig(
        id="fake_mixed",
        collector="fake_mixed",
        category=OpportunityCategory.MIXED,
        url="https://example.com",
    )
    broken_source = SourceConfig(
        id="fake_broken",
        collector="fake_broken",
        category=OpportunityCategory.MIXED,
        url="https://example.com",
    )
    store = RadarStore(tmp_path / "radar.sqlite3")
    store.initialize()

    results = asyncio.run(
        run_collection([mixed_source, broken_source], ProfileRules(), store)
    )

    by_source = {result.source: result for result in results}
    assert by_source["fake_broken"].ok is False
    assert "RuntimeError" in by_source["fake_broken"].message
    assert by_source["fake_mixed"].ok is True

    default_rows = store.list_opportunities()
    assert [row["title"] for row in default_rows] == ["Contract automation developer"]
    assert default_rows[0]["category"] == "contract"
    # Phase 3.2: the pipeline labels and persists service domains.
    assert json.loads(default_rows[0]["service_domains_json"]) == ["automation"]

    audit_rows = store.list_opportunities(include_traditional=True)
    categories = {row["external_id"]: row["category"] for row in audit_rows}
    assert categories == {"job": "traditional_job", "contract": "contract"}
