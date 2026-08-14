"""Offline tests for the deterministic service-domain classifier."""

from global_builder_radar.models import Opportunity, OpportunityCategory
from global_builder_radar.service_domains import SERVICE_DOMAINS, classify_service_domains


def _opportunity(title: str, description: str = "") -> Opportunity:
    return Opportunity(
        source="test",
        category=OpportunityCategory.FREELANCE,
        title=title,
        description=description,
        url="https://example.com/work",
    )


def test_exactly_seven_domains_exist() -> None:
    assert SERVICE_DOMAINS == (
        "ai",
        "automation",
        "crm",
        "marketing",
        "programming",
        "revops",
        "scraping",
    )


def test_each_domain_is_detected_from_its_own_signal() -> None:
    samples = {
        "programming": "Backend API integration for a web app",
        "automation": "Automate invoice routing with n8n workflows",
        "scraping": "Web scraping of product catalogs into CSV",
        "ai": "Build a chatbot on top of an LLM",
        "marketing": "SEO audit and email marketing campaign",
        "crm": "HubSpot CRM setup and data cleanup",
        "revops": "RevOps dashboard with lead generation reporting",
    }
    for domain, title in samples.items():
        assert classify_service_domains(_opportunity(title)) == [domain], title


def test_multiple_domains_are_sorted_and_deduplicated() -> None:
    opportunity = _opportunity(
        "Scraping automation",
        "Build a scraper and automate it with webhooks. Scraping again.",
    )
    assert classify_service_domains(opportunity) == ["automation", "scraping"]


def test_unknown_text_stays_unknown() -> None:
    opportunity = _opportunity(
        "Write an X thread about the summit",
        "Short content task, pay in stablecoins.",
    )
    assert classify_service_domains(opportunity) == []


def test_keyword_matching_uses_word_boundaries() -> None:
    # "ai" must not fire inside other words; "bot" must not fire in "chatbot"
    # for automation (chatbot belongs to ai).
    opportunity = _opportunity("Retain a captain for sailing training")
    assert classify_service_domains(opportunity) == []
    chatbot = _opportunity("Customer support chatbot")
    assert classify_service_domains(chatbot) == ["ai"]


def test_labels_come_from_description_and_tags_too() -> None:
    opportunity = _opportunity("Small paid task", "Set up zapier automations.")
    assert classify_service_domains(opportunity) == ["automation"]
    tagged = Opportunity(
        source="test",
        category=OpportunityCategory.BOUNTY,
        title="Small paid task",
        url="https://example.com/work",
        tags=["crm", "hubspot-setup"],
    )
    assert classify_service_domains(tagged) == ["crm"]


def test_domains_do_not_change_opportunity_kind() -> None:
    opportunity = Opportunity(
        source="test",
        category=OpportunityCategory.FREELANCE,
        title="Marketing automation setup",
        url="https://example.com/work",
    )
    classify_service_domains(opportunity)
    assert opportunity.category == OpportunityCategory.FREELANCE
