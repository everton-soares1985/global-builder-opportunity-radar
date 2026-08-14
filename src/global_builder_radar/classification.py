"""Deterministic opportunity-kind classification.

Configuration:
- Pure keyword-signal classification; no network access and no AI.
- Occupational phrases (grant writer, bounty hunter) are not mechanisms.
- Explicit full-time/permanent employment evidence outranks ambiguous
  alternative keywords; otherwise alternative-income signals win so
  contracts and projects survive mixed sources.
- Without signals the source-configured category is reflected, never guessed.
"""

from __future__ import annotations

import re

from global_builder_radar.models import Opportunity, OpportunityCategory

# A keyword immediately followed by one of these nouns describes an
# occupation or community role, not an opportunity mechanism. Applied only
# to the listed categories: "freelance developer" and "contract developer"
# remain genuine alternative-income signals.
_OCCUPATION_BLOCKS: dict[OpportunityCategory, str] = {
    OpportunityCategory.BOUNTY: r"(?![\s-]+(?:hunter|hunters))",
    OpportunityCategory.GRANT: (
        r"(?![\s-]+(?:writer|writers|manager|managers|administrator|"
        r"administrators|coordinator|coordinators|specialist|specialists|"
        r"officer|officers))"
    ),
}

_SIGNALS: tuple[tuple[OpportunityCategory, tuple[str, ...]], ...] = (
    (
        OpportunityCategory.BOUNTY,
        ("bounty", "bounties", "issue reward", "issue rewards", "paid issue", "paid issues"),
    ),
    (
        OpportunityCategory.HACKATHON,
        ("hackathon", "hackfest", "prize pool", "prize track"),
    ),
    (
        OpportunityCategory.GRANT,
        ("grant", "grants", "fellowship", "stipend", "funding for"),
    ),
    (
        OpportunityCategory.PAID_PROGRAM,
        (
            "ambassador",
            "mentorship",
            "builder program",
            "season of docs",
            "paid internship",
            "residency program",
        ),
    ),
    (
        OpportunityCategory.FREELANCE,
        ("freelance", "freelancer", "gig", "hourly rate", "per hour", "fixed price", "/hr"),
    ),
    (
        OpportunityCategory.CONTRACT,
        ("contract", "contractor", "fixed-term", "fixed term", "project-based", "project based"),
    ),
)

_TRADITIONAL_SIGNALS = (
    "full-time",
    "full time",
    "fulltime",
    "permanent role",
    "permanent position",
    "employee",
    "employment",
    "benefits package",
    "401k",
    "visa sponsorship",
    "paid time off",
    "health insurance",
)

# Explicit employment evidence: an employment-form keyword immediately
# followed by employment substance. It outranks ambiguous alternative
# keywords such as a bare "contract" inside "employment contract".
_TRADITIONAL_EVIDENCE = re.compile(
    r"(?i)(?<!\w)(?:full[- ]?time|fulltime|permanent)(?:[\w,\- ]{0,80}?"
    r"(?<!\w)(?:employee|employment|position|role|jobs?|salary|benefits?|401k|"
    r"health insurance|paid time off)\b|(?=[\s-]+(?:employee|employment|"
    r"position|role|jobs?|salary|benefits|401k)))"
)


def _signal_count(haystack: str, keywords: tuple[str, ...], block: str = "") -> int:
    count = 0
    for keyword in keywords:
        escaped = re.escape(keyword.strip().lower()).replace(r"\ ", r"\s+")
        if keyword == "/hr":
            escaped = r"/\s*hr"
        if re.search(rf"(?<!\w){escaped}(?!\w){block}", haystack):
            count += 1
    return count


def classify_opportunity_kind(opportunity: Opportunity) -> OpportunityCategory:
    """Classify the opportunity kind from its own text evidence.

    The current (source-configured) category is the fallback when no
    deterministic signal is present, so unknown text is never guessed away.
    """

    haystack = " ".join(
        [opportunity.title, opportunity.description, " ".join(opportunity.tags)]
    ).lower()
    if _TRADITIONAL_EVIDENCE.search(haystack):
        return OpportunityCategory.TRADITIONAL_JOB
    best_category = None
    best_count = 0
    for category, keywords in _SIGNALS:
        count = _signal_count(haystack, keywords, _OCCUPATION_BLOCKS.get(category, ""))
        if count > best_count:
            best_category = category
            best_count = count
    if best_category is not None:
        return best_category
    if _signal_count(haystack, _TRADITIONAL_SIGNALS) > 0:
        return OpportunityCategory.TRADITIONAL_JOB
    fallback = {
        OpportunityCategory.MIXED: OpportunityCategory.MIXED,
        OpportunityCategory.DIRECT_JOB: OpportunityCategory.TRADITIONAL_JOB,
    }
    return fallback.get(opportunity.category, opportunity.category)
