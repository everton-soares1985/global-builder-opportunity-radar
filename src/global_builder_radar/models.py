"""Domain models shared by collectors and the pipeline.

Configuration:
- No source-specific fields belong in Opportunity.
- Preserve source-only fields inside raw_payload.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, Field, computed_field, field_validator

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "ref",
    "source",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}


class OpportunityCategory(StrEnum):
    FREELANCE = "freelance"
    CONTRACT = "contract"
    BOUNTY = "bounty"
    GRANT = "grant"
    HACKATHON = "hackathon"
    PAID_PROGRAM = "paid_program"
    TRADITIONAL_JOB = "traditional_job"
    DIRECT_JOB = "direct_job"  # legacy alias for traditional employment
    MIXED = "mixed"  # legacy placeholder for unclassified mixed sources


class OpportunityStatus(StrEnum):
    NEW = "new"
    REVIEWED = "reviewed"
    DISCARDED = "discarded"
    ACTIONED = "actioned"


class BrazilEligibility(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    UNKNOWN = "unknown"


def canonicalize_url(value: str) -> str:
    parts = urlsplit(value.strip())
    clean_query = urlencode(
        sorted(
            (key, val)
            for key, val in parse_qsl(parts.query, keep_blank_values=True)
            if key.lower() not in TRACKING_QUERY_KEYS
        )
    )
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, clean_query, ""))


class Opportunity(BaseModel):
    source: str
    category: OpportunityCategory
    external_id: str | None = None
    title: str = Field(min_length=1, max_length=500)
    description: str = ""
    url: str
    contact_type: str | None = None
    contact: str | None = None
    compensation_text: str | None = None
    compensation_amount_min: float | None = None
    compensation_amount_max: float | None = None
    compensation_currency: str | None = None
    compensation_unit: str | None = None
    published_at: datetime | None = None
    deadline: datetime | None = None
    deadline_evidence: str | None = None
    location: str | None = None
    remote: bool | None = None
    technologies: list[str] = Field(default_factory=list)
    effort_evidence: str | None = None
    brazil_eligibility: BrazilEligibility = BrazilEligibility.UNKNOWN
    tags: list[str] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    score: float = 0.0
    status: OpportunityStatus = OpportunityStatus.NEW

    @field_validator("url")
    @classmethod
    def normalize_url(cls, value: str) -> str:
        normalized = canonicalize_url(value)
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("Opportunity URL must be HTTP(S)")
        return normalized

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        return sorted({value.strip().lower() for value in values if value.strip()})

    @field_validator("technologies")
    @classmethod
    def normalize_technologies(cls, values: list[str]) -> list[str]:
        return sorted({value.strip().lower() for value in values if value.strip()})

    @computed_field
    @property
    def fingerprint(self) -> str:
        discriminator = self.external_id or self.url
        material = f"{self.source}|{discriminator}".lower().encode()
        return hashlib.sha256(material).hexdigest()

    def raw_payload_json(self) -> str:
        return json.dumps(self.raw_payload, ensure_ascii=False, default=str, sort_keys=True)


class SourceConfig(BaseModel):
    id: str
    enabled: bool = True
    collector: str
    category: OpportunityCategory
    url: str
    max_items: int = Field(default=50, ge=1, le=500)
    timeout_seconds: float = Field(default=30, gt=0, le=120)
    options: dict[str, Any] = Field(default_factory=dict)


class CollectionResult(BaseModel):
    source: str
    opportunities: list[Opportunity] = Field(default_factory=list)
    ok: bool = True
    message: str = ""
    elapsed_seconds: float = 0.0
