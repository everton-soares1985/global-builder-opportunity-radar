from global_builder_radar.config import ProfileRules
from global_builder_radar.models import Opportunity, OpportunityCategory
from global_builder_radar.scoring import basic_quality, freshness_days, score_opportunity


def test_score_rewards_profile_match_and_direct_contact() -> None:
    opportunity = Opportunity(
        source="test",
        category=OpportunityCategory.FREELANCE,
        title="Python automation and scraping project",
        description="Remote API integration",
        url="https://example.com/job",
        contact_type="email",
        contact="team@example.com",
        remote=True,
    )
    rules = ProfileRules(
        include_keywords={"python": 8, "automation": 8, "scraping": 8},
        bonuses={"email_contact": 6, "remote": 3},
    )
    assert score_opportunity(opportunity, rules) == 33


def test_score_never_goes_below_zero() -> None:
    opportunity = Opportunity(
        source="test",
        category=OpportunityCategory.FREELANCE,
        title="Unpaid volunteer only",
        url="https://example.com/job",
    )
    rules = ProfileRules(exclude_keywords={"unpaid": -20, "volunteer only": -20})
    assert score_opportunity(opportunity, rules) == 0


def test_keyword_matching_uses_word_boundaries() -> None:
    opportunity = Opportunity(
        source="test",
        category=OpportunityCategory.DIRECT_JOB,
        title="Capital markets analyst",
        url="https://example.com/job",
    )
    rules = ProfileRules(include_keywords={"api": 10})
    assert score_opportunity(opportunity, rules) == 0


def test_category_and_source_weights_are_applied() -> None:
    opportunity = Opportunity(
        source="opire_bounties",
        category=OpportunityCategory.BOUNTY,
        title="Small paid task",
        url="https://example.com/bounty",
    )
    rules = ProfileRules(
        category_weights={"bounty": 10},
        source_weights={"opire_bounties": 4},
    )
    assert score_opportunity(opportunity, rules) == 14


def test_basic_quality_counts_four_evidence_checks() -> None:
    long_description = "word " * 30
    assert basic_quality("$500", long_description, "team@example.com", True) == 1.0
    assert basic_quality(None, "short", None, False) == 0.0
    assert basic_quality("$500", "short", None, False) == 0.25
    assert basic_quality(None, long_description, "team@example.com", False) == 0.5


def test_freshness_days_parses_sqlite_and_iso_timestamps() -> None:
    from datetime import UTC, datetime

    now = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
    # SQLite CURRENT_TIMESTAMP format (no timezone, treated as UTC).
    assert freshness_days("2026-08-10 12:00:00", now) == 4
    # ISO format with explicit offset.
    assert freshness_days("2026-08-14T06:00:00+00:00", now) == 0
    # Missing or unparsable evidence stays unknown; future dates clamp to 0.
    assert freshness_days(None, now) is None
    assert freshness_days("not a date", now) is None
    assert freshness_days("2026-09-01 00:00:00", now) == 0
