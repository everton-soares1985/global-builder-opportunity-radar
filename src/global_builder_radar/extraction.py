"""Structured evidence extraction.

Configuration:
- Extract only what the source text states explicitly; unknown stays unknown.
- Raw text evidence remains on the opportunity (compensation_text, deadline_evidence,
  effort_evidence) so parsed values are always reproducible.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from dateutil import parser as date_parser

from global_builder_radar.models import BrazilEligibility, Opportunity

_CURRENCY_SYMBOLS = {
    "$": "USD",
    "US$": "USD",
    "AU$": "AUD",
    "CA$": "CAD",
    "€": "EUR",
    "£": "GBP",
    "R$": "BRL",
}
_CURRENCY_CODES = {"USD", "EUR", "GBP", "BRL", "AUD", "CAD", "USDC", "USDG"}
_CURRENCY_CODE_ALTERNATIVES = "|".join(sorted(_CURRENCY_CODES, key=len, reverse=True))
_AMOUNT = r"\d[\d,.]*"
_RANGE = re.compile(
    rf"(?i)(?P<currency_symbol>US\$|AU\$|CA\$|R\$|\$|€|£)?"
    rf"(?:\s*(?P<currency_prefix>{_CURRENCY_CODE_ALTERNATIVES})(?![\w$]))?\s*"
    rf"(?P<low>{_AMOUNT})\s*(?P<low_magnitude>[kKmM])?"
    rf"(?:\s*(?:-|–|—|to)\s*(?:US\$|AU\$|CA\$|R\$|\$|€|£)?\s*"
    rf"(?P<high>{_AMOUNT})\s*(?P<high_magnitude>[kKmM])?)?"
    rf"(?:\s*(?P<currency_code>{_CURRENCY_CODE_ALTERNATIVES})(?!\w))?"
)
_UNIT_PATTERNS = (
    ("hourly", re.compile(r"(?i)/\s*(?:hr|hour)\b|per\s+hour\b|hourly\b")),
    ("monthly", re.compile(r"(?i)/\s*(?:month|mo)\b|per\s+month\b|monthly\b")),
    ("yearly", re.compile(r"(?i)/\s*year\b|per\s+year\b|annually\b|annual\b")),
)
_MAGNITUDE = {"k": 1_000, "m": 1_000_000}

# A candidate amount is compensation only with a currency or an explicit
# payment context nearby. Corporate metrics and aggregate pools are skipped
# and recorded as discarded evidence instead of being claimed as pay.
_PAY_CONTEXT = re.compile(
    r"(?i)\b(?:per\s+(?:hour|month|year|mo)|hourly|monthly|yearly|annually|"
    r"fixed\s+price|bounty|bounties|reward|rewards|prize|grant|fellowship|"
    r"stipend|salary|rate|budget|pay(?:ment)?|compensation|wages?|payout)\b"
    r"|/\s*(?:hr|hour|month|year|mo)"
)
_BUSINESS_CONTEXT = re.compile(
    r"(?i)\brevenue\b|\barr\b|\bgmv\b|\bvaluation\b|\braised\b|\braising\b|\bfunding\b"
    r"|\bfunded\b|\bmarket\s+size\b|\bseries\s+[a-z]\b|\btransactions?\b|\bturnover\b"
)
_POOL_CONTEXT = re.compile(
    r"(?i)\bprize\s+pool\b|\btotal\s+prize\b|\bpool\s+of\b|\baggregate\b"
)
_INDIVIDUAL_CONTEXT = re.compile(
    r"(?i)\bindividual\b|\bper\s+(?:winner|team|project|recipient|person)\b|\beach\b"
)

_TECHNOLOGY_ALIASES = {
    "python": "python",
    "playwright": "playwright",
    "selenium": "selenium",
    "scrapling": "scrapling",
    "apify": "apify",
    "beautifulsoup": "beautifulsoup",
    "javascript": "javascript",
    "typescript": "typescript",
    "node.js": "node",
    "react": "react",
    "sql": "sql",
    "postgres": "postgres",
    "postgresql": "postgres",
    "docker": "docker",
    "aws": "aws",
    "llm": "llm",
    "openai": "openai",
    "langchain": "langchain",
}

_MONTH = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)
_DEADLINE_CONTEXT = re.compile(
    rf"(?i)(?:deadline|apply\s+(?:by|before)|closes?(?:\s+on)?|ends?\s+on|due\s+(?:by|on)?)"
    rf"[^.;\n]*?(?P<date>\d{{4}}-\d{{2}}-\d{{2}}|\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTH})"
    rf"(?:,?\s+\d{{4}})?|(?:{_MONTH})\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?)"
)
_EFFORT = re.compile(
    r"(?i)(?:estimated|expected|approximately|around|about)\s+"
    r"(?:effort|duration|time)?\s*(?:of|is|:)?\s*"
    r"(?P<amount>\d[\d-]*)\s*(?P<unit>hours?|hrs?|days?|weeks?|months?)"
)
_BRAZIL_EXCLUSION = re.compile(
    r"(?i)\b(?:except|excluding|exclude|without)\s+brazil\b|"
    r"\bnot\s+(?:available|open|eligible|accepting)\s+(?:in|for|to|from)\s+brazil\b|"
    r"\bbrazil\s+is\s+(?:excluded|not\s+eligible)\b"
)
_CITIZENSHIP_ONLY_PATTERN = (
    r"\bus\s+citizens?\s+only\b"
    r"|\bu\.?s\.?\s+(?:citizens?|residents?|applicants?)\s+only\b"
    r"|\bunited\s+states\s+only\b"
)
_REGIONAL_ONLY_PATTERN = (
    r"\bmust\s+be\s+(?:based|located|resident)\s+in\s+(?:the\s+)?"
    r"(?:us|usa|united\s+states|europe|eu|uk|united\s+kingdom|canada|australia)\b"
)
_CITIZENSHIP_ONLY = re.compile(rf"(?i){_CITIZENSHIP_ONLY_PATTERN}")
_REGIONAL_ONLY = re.compile(rf"(?i){_REGIONAL_ONLY_PATTERN}")
_BRAZIL_INELIGIBLE = re.compile(
    rf"(?i){_CITIZENSHIP_ONLY_PATTERN}|{_REGIONAL_ONLY_PATTERN}"
)
# Brazil inside the same regional clause ("Europe or Brazil") is inclusion,
# not contradiction.
_REGION_BRAZIL_CLAUSE = re.compile(r"(?i)\b(?:or|and)\s+brazil|[,+/]\s*brazil")
_BRAZIL_ELIGIBLE = re.compile(
    r"(?i)\blatam\b|\blatin\s+america\b|\bworldwide\b|\bglobal(?:ly)?\b|"
    r"\banywhere\s+in\s+the\s+world\b|\bopen\s+to\s+all\s+countries\b|"
    r"\binternational\s+applicants?\b"
)


def _numeric_value(raw: str) -> float | None:
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", raw):
        raw = raw.replace(".", "")
    elif "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        parts = raw.rsplit(",", 1)
        raw = raw.replace(",", "") if len(parts[1]) == 3 else raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_compensation(text: str) -> tuple[float | None, float | None, str | None, str | None]:
    """Return (amount_min, amount_max, currency, unit) parsed from explicit text.

    Candidates need a currency or explicit payment context, and company
    metrics or aggregate pools are never selected as individual pay.
    """
    parsed, _, _ = parse_compensation_with_evidence(text)
    return parsed


def parse_compensation_with_evidence(
    text: str,
) -> tuple[
    tuple[float | None, float | None, str | None, str | None],
    str | None,
    list[str],
]:
    """Parse compensation and return ``(parsed, selected_snippet, discarded)``.

    ``discarded`` preserves rejected snippets (corporate metrics, aggregate
    pools) so callers can keep the evidence without claiming it as pay.
    """
    discarded: list[str] = []
    for match in _RANGE.finditer(text):
        if not match.group("low"):
            continue
        low = _numeric_value(match.group("low"))
        if low is None:
            continue
        start, end = match.span()
        before = text[max(0, start - 80) : start]
        nearby = text[max(0, start - 40) : min(len(text), end + 40)]
        symbol = match.group("currency_symbol")
        currency = (
            match.group("currency_code")
            or (match.group("currency_prefix") or "").upper() or None
        )
        if currency is None and symbol:
            currency = _CURRENCY_SYMBOLS.get(symbol)
        if currency is None and not _PAY_CONTEXT.search(nearby):
            continue  # bare numbers are never compensation on their own.
        if _BUSINESS_CONTEXT.search(before) and not _PAY_CONTEXT.search(before):
            discarded.append(match.group(0))
            continue
        if _POOL_CONTEXT.search(before) and not _INDIVIDUAL_CONTEXT.search(before):
            discarded.append(match.group(0))
            continue
        low_magnitude = (match.group("low_magnitude") or "").lower()
        high_magnitude = (match.group("high_magnitude") or "").lower()
        amount_min = low * _MAGNITUDE.get(low_magnitude, 1)
        amount_max = amount_min
        if match.group("high"):
            high = _numeric_value(match.group("high"))
            if high is not None:
                if not low_magnitude and high_magnitude:
                    # Range shorthand such as "$1-2k" shares the upper magnitude.
                    amount_min = low * _MAGNITUDE[high_magnitude]
                amount_max = high * _MAGNITUDE.get(high_magnitude or low_magnitude, 1)
        unit = "fixed"
        for unit_name, pattern in _UNIT_PATTERNS:
            if pattern.search(text):
                unit = unit_name
                break
        return (
            (amount_min, amount_max, currency, unit),
            match.group(0).strip(),
            discarded,
        )
    return (None, None, None, None), None, discarded


def extract_technologies(text: str) -> list[str]:
    lowered = text.lower()
    found = set()
    for alias, canonical in _TECHNOLOGY_ALIASES.items():
        escaped = re.escape(alias)
        if re.search(rf"(?<!\w){escaped}(?!\w)", lowered):
            found.add(canonical)
    return sorted(found)


def extract_deadline(text: str) -> tuple[datetime | None, str | None]:
    """Return (deadline, evidence) only when an explicit dated deadline exists."""

    match = _DEADLINE_CONTEXT.search(text)
    if not match:
        return None, None
    try:
        parsed = date_parser.parse(match.group("date"), default=datetime.now(UTC))
    except (ValueError, OverflowError):
        return None, None
    return parsed, match.group(0).strip()


def extract_effort(text: str) -> str | None:
    match = _EFFORT.search(text)
    if not match:
        return None
    return f"{match.group('amount')} {match.group('unit').lower()}"


def explicit_unit(text: str) -> str | None:
    """Return the first explicit pay-period marker, or None when absent."""

    for unit_name, pattern in _UNIT_PATTERNS:
        if pattern.search(text):
            return unit_name
    return None


def assess_brazil_eligibility(text: str) -> BrazilEligibility:
    """Classify Brazil eligibility conservatively from explicit evidence.

    Order is the chosen contract for contradictory text: an explicit Brazil
    exclusion always wins. A Brazil mention is eligible unless a mandatory
    restriction contradicts it: citizenship-only requirements (``US citizens
    only``) can never include Brazil, and regional restrictions contradict
    unless Brazil is named inside the same clause (``Europe or Brazil``).
    Only then do non-Brazil restrictions, worldwide language, or unknown
    apply.
    """
    if _BRAZIL_EXCLUSION.search(text):
        return BrazilEligibility.INELIGIBLE
    if re.search(r"(?i)\bbrazil(?:ian)?s?\b", text):
        if _CITIZENSHIP_ONLY.search(text):
            return BrazilEligibility.INELIGIBLE
        region_match = _REGIONAL_ONLY.search(text)
        if region_match:
            clause_tail = text[region_match.end() : region_match.end() + 40]
            if not _REGION_BRAZIL_CLAUSE.search(clause_tail):
                return BrazilEligibility.INELIGIBLE
        return BrazilEligibility.ELIGIBLE
    if _BRAZIL_INELIGIBLE.search(text):
        return BrazilEligibility.INELIGIBLE
    if _BRAZIL_ELIGIBLE.search(text):
        return BrazilEligibility.ELIGIBLE
    return BrazilEligibility.UNKNOWN


def enrich_opportunity(opportunity: Opportunity) -> None:
    """Fill structured fields from explicit text evidence without overwriting
    values the collector already produced."""

    haystack = " ".join([opportunity.title, opportunity.description])
    if opportunity.compensation_text:
        amount_min, amount_max, currency, unit = parse_compensation(
            opportunity.compensation_text
        )
        if unit == "fixed":
            # Collector snippets can lose the pay-period suffix ("$5/hr" -> "$5"),
            # so an explicit marker in the full evidence wins over the default.
            unit = explicit_unit(haystack) or unit
        if opportunity.compensation_amount_min is None:
            opportunity.compensation_amount_min = amount_min
        if opportunity.compensation_amount_max is None:
            opportunity.compensation_amount_max = amount_max
        if opportunity.compensation_currency is None:
            opportunity.compensation_currency = currency
        if opportunity.compensation_unit is None:
            opportunity.compensation_unit = unit
    if not opportunity.technologies:
        opportunity.technologies = extract_technologies(haystack)
    if opportunity.deadline is None:
        deadline, evidence = extract_deadline(haystack)
        opportunity.deadline = deadline
        if deadline is not None:
            opportunity.deadline_evidence = evidence
    if opportunity.effort_evidence is None:
        opportunity.effort_evidence = extract_effort(haystack)
    if opportunity.brazil_eligibility is BrazilEligibility.UNKNOWN:
        opportunity.brazil_eligibility = assess_brazil_eligibility(haystack)
