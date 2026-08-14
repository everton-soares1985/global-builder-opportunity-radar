"""Collector protocol and shared extraction helpers.

Configuration:
- User-Agent identifies the project without containing credentials.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from global_builder_radar.models import CollectionResult, SourceConfig

EMAIL_PATTERN = re.compile(r"(?<![\w.+-])([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})(?![\w.-])")
_CURRENCY = r"(?:US\$|AU\$|CA\$|R\$|USD|EUR|BRL|GBP|\$|€|£)"
_TOKEN_CURRENCY = r"(?:USDC|USDG|USD|EUR|BRL|GBP)"
_AMOUNT = r"(?:\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)"
_MAGNITUDE = r"(?:[kKmMbBtT])?"
MONEY_PATTERN = re.compile(
    rf"(?i)(?:"
    rf"{_CURRENCY}\s*{_AMOUNT}{_MAGNITUDE}\+?"
    rf"(?:\s*(?:-|–|—|to)\s*(?:{_CURRENCY}\s*)?{_AMOUNT}{_MAGNITUDE}\+?)?"
    rf"(?:\s*{_TOKEN_CURRENCY})?"
    rf"|{_AMOUNT}{_MAGNITUDE}\+?"
    rf"(?:\s*(?:-|–|—|to)\s*{_AMOUNT}{_MAGNITUDE}\+?)?\s*{_TOKEN_CURRENCY}"
    rf")"
)

_PAY_CONTEXT = re.compile(
    r"(?i)\b(?:salary|compensation|pay|base|budget|bounty|reward|prize|grant|rate|"
    r"full[- ]time|part[- ]time|contract|hourly|per\s+(?:hour|month|year)|equity)\b|/hr"
)
_DIRECT_PAY_CONTEXT = re.compile(
    r"(?i)\b(?:salary|compensation|base\s+(?:pay|salary)|budget|bounty|reward|prize|grant|"
    r"hourly\s+rate|pay\s+range|salary\s+range|per\s+(?:hour|month|year))\b|/hr"
)
_BUSINESS_VALUE_CONTEXT = re.compile(
    r"(?i)\b(?:arr|gmv|revenue|valuation|raised|raising|funding|funded|series\s+[a-z]|"
    r"industry|market\s+size|transactions?|sales\s+volume|contracted\s+revenue)\b"
)
_POOL_CONTEXT = re.compile(r"(?i)\b(?:prize\s+pool|total\s+prize|pool\s+of|aggregate)\b")
_INDIVIDUAL_CONTEXT = re.compile(
    r"(?i)\b(?:individual|per\s+(?:winner|team|project|recipient|person)|each)\b"
)
_STABLECOIN = re.compile(r"(?i)\b(?:USDC|USDG)\b")


def _numeric_value(value: str) -> float:
    number = re.search(r"\d[\d,.]*", value)
    if not number:
        return 0
    raw = number.group(0)
    if ("," in raw and "." in raw) or (
        raw.count(",") == 1 and len(raw.rsplit(",", 1)[1]) == 3
    ):
        raw = raw.replace(",", "")
    else:
        raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return 0


def first_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)
    return match.group(1) if match else None


def first_compensation(text: str) -> str | None:
    """Return the first likely individual payment amount.

    Company-value figures and aggregate prize pools are skipped; only the
    text immediately before an amount decides its context.
    """

    for match in MONEY_PATTERN.finditer(text):
        value = match.group(0).strip().rstrip(".,;:")
        context = text[max(0, match.start() - 120) : min(len(text), match.end() + 120)]
        before = text[max(0, match.start() - 80) : match.start()]
        if _STABLECOIN.search(value):
            return value
        if _POOL_CONTEXT.search(before) and not _INDIVIDUAL_CONTEXT.search(before):
            continue
        if _BUSINESS_VALUE_CONTEXT.search(before) and not _DIRECT_PAY_CONTEXT.search(before):
            continue
        magnitude = re.search(r"(?i)\d[\d,.]*\s*([kmbt])", value)
        if (
            magnitude
            and magnitude.group(1).lower() in {"m", "b", "t"}
            and not _DIRECT_PAY_CONTEXT.search(context)
        ):
            continue
        if _numeric_value(value) < 10 and not _PAY_CONTEXT.search(context):
            continue
        return value
    return None


class Collector(ABC):
    def __init__(self, source: SourceConfig) -> None:
        self.source = source

    @abstractmethod
    async def collect(self) -> CollectionResult:
        """Collect opportunities without mutating external systems."""
