from datetime import UTC, datetime

import pytest

from global_builder_radar.extraction import (
    assess_brazil_eligibility,
    enrich_opportunity,
    extract_deadline,
    extract_effort,
    extract_technologies,
    parse_compensation,
)
from global_builder_radar.models import BrazilEligibility, Opportunity, OpportunityCategory


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("$500", (500.0, 500.0, "USD", "fixed")),
        ("USD 1,500", (1500.0, 1500.0, "USD", "fixed")),
        ("USD 130.00", (130.0, 130.0, "USD", "fixed")),
        ("$1,500-2,000 per month", (1500.0, 2000.0, "USD", "monthly")),
        ("€3k", (3000.0, 3000.0, "EUR", "fixed")),
        ("500 USDC", (500.0, 500.0, "USDC", "fixed")),
        ("R$ 3.000", (3000.0, 3000.0, "BRL", "fixed")),
        ("$45/hour", (45.0, 45.0, "USD", "hourly")),
        ("competitive pay, equity included", (None, None, None, None)),
        ("", (None, None, None, None)),
    ],
)
def test_parse_compensation(text: str, expected: tuple) -> None:
    assert parse_compensation(text) == expected


def test_extract_technologies_matches_word_boundaries() -> None:
    assert extract_technologies("Python and Playwright automation") == [
        "playwright",
        "python",
    ]
    assert extract_technologies("Pythons are great pets") == []


def test_extract_deadline_requires_explicit_date() -> None:
    deadline, evidence = extract_deadline("Apply by 30 August 2026 via the form.")
    assert deadline is not None
    assert (deadline.year, deadline.month, deadline.day) == (2026, 8, 30)
    assert deadline.tzinfo is not None
    assert evidence is not None
    assert extract_deadline("Deadline to be announced soon.") == (None, None)
    assert extract_deadline("No timing mentioned at all.") == (None, None)


def test_extract_effort_only_when_explicit() -> None:
    assert extract_effort("Estimated effort: 20 hours") == "20 hours"
    assert extract_effort("Expected duration of 3 weeks") == "3 weeks"
    assert extract_effort("Big project with lots of work") is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("US citizens only", BrazilEligibility.INELIGIBLE),
        ("Must be based in the United States", BrazilEligibility.INELIGIBLE),
        ("Open worldwide, remote first", BrazilEligibility.ELIGIBLE),
        ("Accepting applicants from Brazil and LatAm", BrazilEligibility.ELIGIBLE),
        ("Details inside the thread", BrazilEligibility.UNKNOWN),
    ],
)
def test_brazil_eligibility(text: str, expected: BrazilEligibility) -> None:
    assert assess_brazil_eligibility(text) == expected


def test_enrich_keeps_collector_provided_values() -> None:
    collector_deadline = datetime(2026, 9, 1, tzinfo=UTC)
    opportunity = Opportunity(
        source="test",
        category=OpportunityCategory.BOUNTY,
        title="Python scraping bounty",
        description="Apply by 30 August 2026. Open worldwide.",
        url="https://example.com/bounty",
        compensation_text="$750",
        compensation_currency="USDC",
        deadline=collector_deadline,
        brazil_eligibility=BrazilEligibility.UNKNOWN,
    )
    enrich_opportunity(opportunity)

    assert opportunity.compensation_amount_min == 750.0
    assert opportunity.compensation_currency == "USDC"  # collector value preserved
    assert opportunity.compensation_unit == "fixed"
    assert opportunity.deadline == collector_deadline  # collector value preserved
    assert opportunity.deadline_evidence is None
    assert opportunity.technologies == ["python"]
    assert opportunity.brazil_eligibility is BrazilEligibility.ELIGIBLE


def test_enrich_leaves_unknown_fields_unknown() -> None:
    opportunity = Opportunity(
        source="test",
        category=OpportunityCategory.MIXED,
        title="Unclear listing",
        description="Details announced later.",
        url="https://example.com/unclear",
    )
    enrich_opportunity(opportunity)

    assert opportunity.compensation_amount_min is None
    assert opportunity.deadline is None
    assert opportunity.effort_evidence is None
    assert opportunity.technologies == []
    assert opportunity.brazil_eligibility is BrazilEligibility.UNKNOWN
