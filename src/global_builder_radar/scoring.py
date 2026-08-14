"""Deterministic opportunity scoring.

Configuration:
- Weights are loaded from config/profile_rules.yaml.
- AI scoring is intentionally outside the MVP core.
"""

from __future__ import annotations

import re

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
