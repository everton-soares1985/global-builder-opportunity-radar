"""Offline regression tests for docs/review-findings.md (review 2026-08-13).

Each test maps to one blocking finding and documents the chosen behavior,
including the conservative contract for contradictory eligibility text.
"""

import pytest

from global_builder_radar.classification import classify_opportunity_kind
from global_builder_radar.collectors.base import first_compensation
from global_builder_radar.extraction import (
    assess_brazil_eligibility,
    parse_compensation,
    parse_compensation_with_evidence,
)
from global_builder_radar.models import BrazilEligibility, Opportunity, OpportunityCategory


def _opportunity(title: str, description: str) -> Opportunity:
    return Opportunity(
        source="review",
        category=OpportunityCategory.MIXED,
        title=title,
        description=description,
        url="https://example.com/review",
    )


# --- Blocking: opportunity-kind classification ------------------------------


def test_strong_traditional_evidence_beats_ambiguous_contract() -> None:
    opportunity = _opportunity(
        "Full-time software engineer",
        "Permanent employment contract with health insurance.",
    )
    assert classify_opportunity_kind(opportunity) == OpportunityCategory.TRADITIONAL_JOB


def test_permanent_grant_writer_job_is_not_a_grant() -> None:
    opportunity = _opportunity(
        "Permanent Grant Writer",
        "Salaried grant writer role with benefits.",
    )
    result = classify_opportunity_kind(opportunity)
    assert result is not OpportunityCategory.GRANT
    assert result == OpportunityCategory.TRADITIONAL_JOB


def test_bounty_hunter_employee_is_not_a_bounty() -> None:
    opportunity = _opportunity(
        "Bounty Hunter",
        "Employee role with a monthly salary.",
    )
    result = classify_opportunity_kind(opportunity)
    assert result is not OpportunityCategory.BOUNTY
    assert result == OpportunityCategory.TRADITIONAL_JOB


@pytest.mark.parametrize(
    ("title", "description", "expected"),
    [
        (
            "Three-month project-based contractor engagement",
            "Issue rewards paid on merge. Python preferred.",
            OpportunityCategory.CONTRACT,
        ),
        (
            "Grant applications open",
            "Apply with your open-source project for monthly support.",
            OpportunityCategory.GRANT,
        ),
        (
            "Hackathon with prizes",
            "Online hackathon with a prize pool of $10,000.",
            OpportunityCategory.HACKATHON,
        ),
    ],
)
def test_real_engagement_mechanisms_preserved(
    title: str, description: str, expected: OpportunityCategory
) -> None:
    assert classify_opportunity_kind(_opportunity(title, description)) == expected


# --- Blocking: structured compensation --------------------------------------


def test_date_is_not_compensation() -> None:
    assert parse_compensation("30 August 2026") == (None, None, None, None)


def test_range_shorthand_shares_upper_magnitude() -> None:
    assert parse_compensation("$1-2k") == (1000.0, 2000.0, "USD", "fixed")


def test_company_metric_is_not_individual_pay() -> None:
    assert parse_compensation("Revenue $3M, bounty $100") == (100.0, 100.0, "USD", "fixed")
    parsed, selected, discarded = parse_compensation_with_evidence("Revenue $3M, bounty $100")
    assert parsed == (100.0, 100.0, "USD", "fixed")
    assert selected == "$100"
    assert discarded == ["$3M"]


def test_aggregate_pool_is_not_individual_pay() -> None:
    text = "Prize pool $5M; individual reward $500"
    assert parse_compensation(text) == (500.0, 500.0, "USD", "fixed")
    parsed, selected, discarded = parse_compensation_with_evidence(text)
    assert selected == "$500"
    assert discarded == ["$5M"]


def test_collector_evidence_selection_skips_pools_and_metrics() -> None:
    assert first_compensation("Revenue $3M, bounty $100") == "$100"
    assert first_compensation("Prize pool $5M; individual reward $500") == "$500"


# --- Blocking: Brazil eligibility --------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Must be based in Europe or Brazil", BrazilEligibility.ELIGIBLE),
        ("Worldwide except Brazil", BrazilEligibility.INELIGIBLE),
        # Contradictory text: an explicit Brazil exclusion always wins.
        ("Open worldwide. Not available in Brazil.", BrazilEligibility.INELIGIBLE),
        # Second audit (2026-08-13): a mandatory citizenship restriction can
        # never include Brazil, so it contradicts the Brazil inclusion.
        ("Open to Brazil, US citizens only", BrazilEligibility.INELIGIBLE),
        ("Open to Brazil. Must be based in the United States.", BrazilEligibility.INELIGIBLE),
    ],
)
def test_brazil_eligibility_review_cases(text: str, expected: BrazilEligibility) -> None:
    assert assess_brazil_eligibility(text) == expected
