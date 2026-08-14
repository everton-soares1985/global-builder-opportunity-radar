"""GitHub issue state verification for ledger rows.

Aggregators can keep advertising a bounty after the GitHub issue was
closed or relabeled as zero-bounty. The stored evidence cannot carry that
state, so the GitHub public API is the only trustworthy source:

- Closed rows become status='discarded' (hidden from reports, preserved).
- Open zero-bounty rows lose their compensation fields (never shown paid).
"""

from __future__ import annotations

import re
from typing import Any

_GITHUB_ISSUE_URL = re.compile(
    r"^https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)/?$"
)
_ZERO_BOUNTY_LABEL = re.compile(r"(?i)\bzero[- ]?bounty\b")


def github_issue_api_url(url: str) -> str | None:
    """Return the public REST API URL for a GitHub issue link, if any."""

    match = _GITHUB_ISSUE_URL.match(url.strip())
    if not match:
        return None
    owner, repo, number = match.groups()
    return f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"


def is_zero_bounty(labels: list[dict[str, Any]]) -> bool:
    """Return True when a label marks the issue as having no monetary reward."""

    for label in labels:
        if isinstance(label, dict) and _ZERO_BOUNTY_LABEL.search(str(label.get("name") or "")):
            return True
    return False


def verdict_from_payload(payload: dict[str, Any]) -> tuple[bool, bool]:
    """Return ``(closed, zero_bounty)`` for a GitHub issue API payload."""

    labels = payload.get("labels")
    closed = str(payload.get("state") or "").lower() == "closed"
    return closed, is_zero_bounty(labels if isinstance(labels, list) else [])
