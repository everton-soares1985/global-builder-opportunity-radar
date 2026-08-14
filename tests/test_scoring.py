from global_builder_radar.config import ProfileRules
from global_builder_radar.models import Opportunity, OpportunityCategory
from global_builder_radar.scoring import score_opportunity


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
