"""Deterministic service-domain classification.

Configuration:
- Pure keyword-signal classification; no network access and no AI.
- Exactly seven domains exist in Phase 3.2; anything else stays unknown
  (empty list) and is never guessed.
- Service domain describes the kind of work; opportunity kind and the
  traditional-job quarantine stay separate and unchanged.
"""

from __future__ import annotations

import re

from global_builder_radar.models import Opportunity

SERVICE_DOMAINS: tuple[str, ...] = (
    "ai",
    "automation",
    "crm",
    "marketing",
    "programming",
    "revops",
    "scraping",
)

_DOMAIN_SIGNALS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "programming",
        (
            "programming",
            "programmer",
            "backend",
            "frontend",
            "full-stack",
            "full stack",
            "web development",
            "software development",
            "api integration",
            "bug fix",
            "web app",
            "webapp",
            "mobile app",
            "smart contract",
            "plugin",
            "code review",
        ),
    ),
    (
        "automation",
        (
            "automation",
            "automate",
            "automated",
            "workflow",
            "zapier",
            "n8n",
            "webhook",
            "bot",
        ),
    ),
    (
        "scraping",
        (
            "scraping",
            "scraper",
            "scrape",
            "web scraping",
            "data extraction",
            "crawler",
            "crawl",
        ),
    ),
    (
        "ai",
        (
            "ai",
            "llm",
            "gpt",
            "openai",
            "machine learning",
            "deep learning",
            "chatbot",
            "prompt engineering",
            "fine-tuning",
            "fine tuning",
            "computer vision",
            "neural",
        ),
    ),
    (
        "marketing",
        (
            "marketing",
            "seo",
            "social media",
            "email marketing",
            "campaign",
            "newsletter",
            "copywriting",
            "growth marketing",
        ),
    ),
    (
        "crm",
        (
            "crm",
            "hubspot",
            "salesforce",
            "pipedrive",
            "zoho",
            "attio",
        ),
    ),
    (
        "revops",
        (
            "revops",
            "revenue operations",
            "sales ops",
            "sales operations",
            "lead generation",
            "lead gen",
            "sales enablement",
        ),
    ),
)


def _contains_keyword(haystack: str, keyword: str) -> bool:
    escaped = re.escape(keyword.strip().lower()).replace(r"\ ", r"\s+")
    return bool(escaped and re.search(rf"(?<!\w){escaped}(?!\w)", haystack))


def classify_service_domains(opportunity: Opportunity) -> list[str]:
    """Return the sorted service domains signaled by the opportunity text.

    An empty list means unknown; labels never influence quarantine, scoring,
    or opportunity kind.
    """

    haystack = " ".join(
        [opportunity.title, opportunity.description, " ".join(opportunity.tags)]
    ).lower()
    return sorted(
        domain
        for domain, keywords in _DOMAIN_SIGNALS
        if any(_contains_keyword(haystack, keyword) for keyword in keywords)
    )
