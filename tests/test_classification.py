import json
from pathlib import Path

import pytest

from global_builder_radar.classification import classify_opportunity_kind
from global_builder_radar.models import Opportunity, OpportunityCategory

FIXTURE = Path(__file__).parent / "fixtures" / "opportunity_kind_samples.json"


def _load_samples() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("sample", _load_samples(), ids=lambda item: item["name"])
def test_fixture_samples_classify_deterministically(sample: dict) -> None:
    opportunity = Opportunity(
        source="fixture",
        category=OpportunityCategory(sample["source_category"]),
        title=sample["title"],
        description=sample["description"],
        url="https://example.com/fixture",
        tags=sample["tags"],
    )
    assert classify_opportunity_kind(opportunity) == OpportunityCategory(sample["expected"])


def test_explicit_employment_evidence_outranks_ambiguous_keywords() -> None:
    opportunity = Opportunity(
        source="fixture",
        category=OpportunityCategory.MIXED,
        title="Full-time bounty writer wanted",
        description="Permanent position paying a bounty per accepted article.",
        url="https://example.com/mixed",
    )
    assert classify_opportunity_kind(opportunity) == OpportunityCategory.TRADITIONAL_JOB


def test_contract_survives_full_time_without_employment_substance() -> None:
    opportunity = Opportunity(
        source="fixture",
        category=OpportunityCategory.MIXED,
        title="Full-time contract developer for a 6-month engagement",
        description="Contract work on a data platform, remote friendly.",
        url="https://example.com/contract",
    )
    assert classify_opportunity_kind(opportunity) == OpportunityCategory.CONTRACT


def test_no_signal_keeps_specific_source_category() -> None:
    opportunity = Opportunity(
        source="fixture",
        category=OpportunityCategory.HACKATHON,
        title="Unclear listing",
        description="Details announced later.",
        url="https://example.com/unclear",
    )
    assert classify_opportunity_kind(opportunity) == OpportunityCategory.HACKATHON
