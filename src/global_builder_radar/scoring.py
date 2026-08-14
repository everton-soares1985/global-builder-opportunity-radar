"""Deterministic opportunity scoring.

Configuration:
- Weights are loaded from config/profile_rules.yaml.
- AI scoring is intentionally outside the MVP core.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from global_builder_radar.config import ProfileRules
from global_builder_radar.models import Opportunity


def _contains_keyword(haystack: str, keyword: str) -> bool:
    escaped = re.escape(keyword.strip().lower()).replace(r"\ ", r"\s+")
    return bool(escaped and re.search(rf"(?<!\w){escaped}(?!\w)", haystack))


def score_opportunity(opportunity: Opportunity, rules: ProfileRules) -> float:
    haystack = " ".join(
        [opportunity.title, opportunity.description, " ".join(opportunity.tags)]
    ).lower()
    score = sum(
        weight
        for keyword, weight in rules.include_keywords.items()
        if _contains_keyword(haystack, keyword)
    )
    score += sum(
        weight
        for keyword, weight in rules.exclude_keywords.items()
        if _contains_keyword(haystack, keyword)
    )
    score += rules.category_weights.get(opportunity.category.value, 0)
    score += rules.source_weights.get(opportunity.source, 0)
    if opportunity.contact_type == "email":
        score += rules.bonuses.get("email_contact", 0)
    elif opportunity.contact_type:
        score += rules.bonuses.get("direct_contact", 0)
    if opportunity.compensation_text:
        score += rules.bonuses.get("compensation_visible", 0)
    if opportunity.remote:
        score += rules.bonuses.get("remote", 0)
    if opportunity.deadline:
        score += rules.bonuses.get("deadline_visible", 0)
    return max(0.0, round(score, 2))


def basic_quality(
    compensation_text: str | None,
    description: str,
    contact: str | None,
    date_evidence: bool,
) -> float:
    """Basic evidence completeness: four deterministic checks, 0.25 each.

    This is a reporting signal only; it never feeds ranking or quarantine.
    """

    checks = (
        bool(compensation_text),
        len(" ".join(description.split())) >= 80,
        bool(contact),
        date_evidence,
    )
    return round(sum(checks) / len(checks), 2)


def freshness_days(reference: str | None, now: datetime) -> int | None:
    """Age in days from an ISO-ish timestamp string; None without evidence.

    Timestamps without a timezone are treated as UTC (SQLite
    CURRENT_TIMESTAMP format).
    """

    if not reference:
        return None
    try:
        parsed = datetime.fromisoformat(reference)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return max(0, (now - parsed).days)
