"""Local HTML briefing renderer (Phase 4A).

Pure, deterministic rendering from stored ledger rows. No network access,
no database writes, no AI: every surfaced fact comes from SQLite evidence,
unknown values stay `Unknown`, and every source-derived value is escaped.
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any

from global_builder_radar.scoring import basic_quality, freshness_days

UNKNOWN = "Unknown"
GROUP_ORDER = ("ready", "needs_details", "brazil_unavailable")
GROUP_TITLES = {
    "ready": "Ready to review",
    "needs_details": "Needs details",
    "brazil_unavailable": "Brazil unavailable",
}
GROUP_NOTES = {
    "ready": "Stored pay evidence and no explicit Brazil ineligibility.",
    "needs_details": "Payment, deadline, eligibility, or contact evidence is missing.",
    "brazil_unavailable": "Explicitly marked unavailable for Brazil; kept visible for audit.",
}
_EXCERPT_LENGTH = 300


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _json_list(raw: Any) -> list[str]:
    try:
        parsed = json.loads(raw or "[]")
    except (json.JSONDecodeError, TypeError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _or_unknown(value: Any) -> str:
    text = str(value).strip() if value is not None else ""
    return text or UNKNOWN


def row_view(row: dict, now: datetime) -> dict:
    """Normalize a stored ledger row into the fields the briefing renders."""
    age = freshness_days(row.get("published_at"), now)
    if age is None:
        age = freshness_days(row.get("first_seen_at"), now)
    quality = basic_quality(
        row.get("compensation_text"),
        row.get("description") or "",
        row.get("contact"),
        bool(row.get("published_at") or row.get("deadline")),
    )
    eligibility = (row.get("brazil_eligibility") or "unknown").strip().lower()
    view = {
        "title": _or_unknown(row.get("title")),
        "source": _or_unknown(row.get("source")),
        "kind": _or_unknown(row.get("category")),
        "url": row.get("url") or "",
        "domains": _json_list(row.get("service_domains_json")),
        "technologies": _json_list(row.get("technologies_json")),
        "score": row.get("score"),
        "age_days": age,
        "quality": quality,
        "pay": row.get("compensation_text"),
        "deadline": row.get("deadline"),
        "eligibility": eligibility,
        "location": row.get("location"),
        "remote": row.get("remote"),
        "effort": row.get("effort_evidence"),
        "contact": row.get("contact") or row.get("contact_type"),
        "description": " ".join((row.get("description") or "").split()),
    }
    view["group"] = review_group(view)
    return view


def review_group(view: dict) -> str:
    """Factual review priority: never inferred beyond stored evidence."""
    if view["eligibility"] == "ineligible":
        return "brazil_unavailable"
    if view["pay"]:
        return "ready"
    return "needs_details"


def why_surfaced(view: dict) -> list[str]:
    reasons = []
    if view["score"] is not None:
        reasons.append(f"Deterministic profile score: {view['score']}.")
    if view["pay"]:
        reasons.append(f"Stored pay evidence: {view['pay']}.")
    if view["domains"]:
        reasons.append(f"Service domains matched: {', '.join(view['domains'])}.")
    if view["age_days"] is not None:
        reasons.append(f"Evidence age: {view['age_days']} day(s).")
    if view["deadline"]:
        reasons.append("Deadline evidence stored.")
    if view["contact"]:
        reasons.append("Contact path stored.")
    if not reasons:
        reasons.append("Listed by an enabled alternative-income source.")
    return reasons


def next_actions(view: dict) -> list[str]:
    if view["group"] == "brazil_unavailable":
        return [
            "Stored evidence marks this listing unavailable for Brazil; do not apply "
            "unless the original listing says otherwise.",
            "Open the original opportunity to inspect it for audit only.",
        ]
    actions = ["Open the original opportunity and confirm it is still available."]
    if view["contact"]:
        actions.append(f"Use the stated contact path: {view['contact']}.")
    missing = []
    if not view["pay"]:
        missing.append("pay")
    if not view["deadline"]:
        missing.append("deadline")
    if view["eligibility"] == "unknown":
        missing.append("Brazil eligibility")
    if not view["contact"]:
        missing.append("contact path")
    if missing:
        actions.append(
            "Verify these missing details in the original listing before applying: "
            f"{', '.join(missing)}."
        )
    return actions


def filter_views(
    views: list[dict],
    *,
    min_score: float = 0,
    paid_only: bool = False,
    max_age_days: int | None = None,
    limit: int = 0,
) -> list[dict]:
    selected = []
    for view in views:
        score = view["score"] if view["score"] is not None else 0
        if score < min_score:
            continue
        if paid_only and not view["pay"]:
            continue
        if max_age_days is not None:
            age = view["age_days"]
            if age is None or age > max_age_days:
                continue
        selected.append(view)
    if limit > 0:
        selected = selected[:limit]
    return selected


def _excerpt(description: str) -> str:
    if len(description) <= _EXCERPT_LENGTH:
        return description or UNKNOWN
    return description[: _EXCERPT_LENGTH - 1].rstrip() + "…"


def _evidence_item(label: str, value: Any) -> str:
    return f'<dt>{_escape(label)}</dt><dd>{_escape(_or_unknown(value))}</dd>'


def _safe_href(url: str) -> str:
    if url.startswith(("http://", "https://")):
        return _escape(url)
    return ""


def render_card(view: dict) -> str:
    href = _safe_href(view["url"])
    link = (
        f'<a class="open-link" href="{href}" target="_blank" rel="noopener noreferrer">'
        "Open original opportunity</a>"
        if href
        else f'<span class="open-link missing">{UNKNOWN} original URL</span>'
    )
    remote = view["remote"]
    remote_text = {True: "Remote", False: "On-site", None: UNKNOWN}[remote]
    location = _or_unknown(view["location"])
    if location != UNKNOWN and remote_text != UNKNOWN:
        location_remote = f"{location} ({remote_text})"
    elif location != UNKNOWN:
        location_remote = location
    else:
        location_remote = remote_text
    evidence = "".join(
        [
            _evidence_item("Pay", view["pay"]),
            _evidence_item("Deadline", view["deadline"]),
            _evidence_item("Brazil eligibility", view["eligibility"]),
            _evidence_item("Location / remote", location_remote),
            _evidence_item("Technologies", ", ".join(view["technologies"]) or None),
            _evidence_item("Effort", view["effort"]),
            _evidence_item("Contact path", view["contact"]),
        ]
    )
    domains = ", ".join(view["domains"]) or None
    meta = "".join(
        [
            _evidence_item("Source", view["source"]),
            _evidence_item("Kind", view["kind"]),
            _evidence_item("Domains", domains),
            _evidence_item("Score", view["score"]),
            _evidence_item("Age (days)", view["age_days"]),
            _evidence_item("Quality", f"{view['quality']:.2f}"),
        ]
    )
    why_items = "".join(f"<li>{_escape(reason)}</li>" for reason in why_surfaced(view))
    action_items = "".join(f"<li>{_escape(action)}</li>" for action in next_actions(view))
    description_block = (
        f'<details><summary>Full original description</summary>'
        f"<p>{_escape(view['description'])}</p></details>"
        if view["description"]
        else ""
    )
    return (
        f'<article class="card" data-source="{_escape(view["source"])}">'
        f'<h3>{_escape(view["title"])}</h3>'
        f'<dl class="meta">{meta}</dl>'
        f'<dl class="evidence">{evidence}</dl>'
        f'<p class="excerpt">{_escape(_excerpt(view["description"]))}</p>'
        f"{description_block}"
        f'<section class="why"><h4>Why it surfaced</h4><ul>{why_items}</ul></section>'
        f'<section class="next"><h4>Next action</h4><ul>{action_items}</ul></section>'
        f"{link}"
        f"</article>"
    )


def describe_filters(
    *,
    paid_only: bool,
    min_score: float,
    max_age_days: int | None,
    limit: int,
) -> str:
    parts = [
        f"paid-only: {'yes' if paid_only else 'no'}",
        f"min-score: {min_score:g}",
        f"max-age: {max_age_days if max_age_days is not None else 'none'} day(s)",
        f"limit: {limit if limit > 0 else 'none'}",
    ]
    return "; ".join(parts)


def render_briefing(
    views: list[dict],
    *,
    generated_at: datetime,
    paid_only: bool = False,
    min_score: float = 0,
    max_age_days: int | None = None,
    limit: int = 0,
) -> str:
    """Render the self-contained private HTML briefing from prepared views."""
    grouped: dict[str, list[dict]] = {key: [] for key in GROUP_ORDER}
    for view in views:
        grouped[view["group"]].append(view)
    sections = []
    for key in GROUP_ORDER:
        cards = grouped[key]
        if not cards:
            continue
        rendered = "".join(render_card(view) for view in cards)
        sections.append(
            f'<section class="group" data-group="{key}">'
            f"<h2>{_escape(GROUP_TITLES[key])} "
            f'<span class="count">({len(cards)})</span></h2>'
            f'<p class="group-note">{_escape(GROUP_NOTES[key])}</p>'
            f"{rendered}</section>"
        )
    body = "".join(sections) or (
        '<p class="empty">No eligible opportunities match the current filters.</p>'
    )
    timestamp = generated_at.astimezone().isoformat(timespec="seconds")
    filters_text = describe_filters(
        paid_only=paid_only, min_score=min_score, max_age_days=max_age_days, limit=limit
    )
    sources = sorted({view["source"] for view in views})
    source_options = "".join(
        f'<option value="{_escape(source)}">{_escape(source)}</option>' for source in sources
    )
    controls = (
        '<div class="controls">'
        '<label for="filter-text">Filter text '
        '<input id="filter-text" type="search" placeholder="title, description, domain…">'
        "</label>"
        '<label for="filter-source">Source '
        f'<select id="filter-source"><option value="">All sources</option>{source_options}'
        "</select></label></div>"
        if views
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Global Builder Opportunity Briefing</title>
<style>
:root {{
  color-scheme: light dark;
  --bg: #f6f7f9; --panel: #ffffff; --ink: #16202b; --muted: #55606c;
  --accent: #0b57d0; --border: #d7dce2;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #10151b; --panel: #1a2129; --ink: #e8edf2; --muted: #9aa7b4;
    --accent: #8ab4f8; --border: #313b46;
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: 1.5rem; background: var(--bg); color: var(--ink);
  font-family: system-ui, "Segoe UI", sans-serif; line-height: 1.5;
}}
main {{ max-width: 60rem; margin: 0 auto; }}
h1 {{ margin: 0 0 0.25rem; font-size: 1.5rem; }}
header p {{ margin: 0.25rem 0; color: var(--muted); }}
.disclaimer {{
  background: var(--panel); border-left: 4px solid var(--accent);
  padding: 0.5rem 0.75rem; border-radius: 4px; color: var(--ink);
}}
.controls {{
  display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0;
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 8px; padding: 0.75rem;
}}
.controls label {{ display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.85rem; }}
.controls input, .controls select {{
  padding: 0.4rem 0.5rem; border: 1px solid var(--border); border-radius: 6px;
  background: var(--bg); color: var(--ink); min-width: 14rem;
}}
.group {{ margin-top: 1.5rem; }}
.group h2 {{ font-size: 1.2rem; margin-bottom: 0.1rem; }}
.group .count {{ color: var(--muted); font-weight: normal; }}
.group-note {{ margin: 0 0 0.75rem; color: var(--muted); font-size: 0.9rem; }}
.card {{
  background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
  padding: 1rem; margin-bottom: 1rem;
}}
.card h3 {{ margin: 0 0 0.5rem; font-size: 1.05rem; }}
dl {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: 0.25rem 1rem; margin: 0.5rem 0; }}
dt {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--muted); }}
dd {{ margin: 0; font-size: 0.92rem; overflow-wrap: anywhere; }}
.excerpt {{ color: var(--muted); font-size: 0.92rem; overflow-wrap: anywhere; }}
details {{ margin: 0.5rem 0; }}
details summary {{ cursor: pointer; color: var(--accent); font-size: 0.9rem; }}
details p {{ white-space: pre-wrap; overflow-wrap: anywhere; font-size: 0.9rem; }}
.why, .next {{ margin-top: 0.5rem; }}
.why h4, .next h4 {{ margin: 0.4rem 0 0.2rem; font-size: 0.9rem; }}
.why ul, .next ul {{ margin: 0; padding-left: 1.2rem; font-size: 0.9rem; }}
.open-link {{
  display: inline-block; margin-top: 0.6rem; color: var(--accent);
  font-weight: 600; text-decoration: none; overflow-wrap: anywhere;
}}
.open-link:hover {{ text-decoration: underline; }}
.open-link.missing {{ color: var(--muted); font-weight: normal; }}
.empty {{ color: var(--muted); }}
footer {{ margin-top: 2rem; color: var(--muted); font-size: 0.85rem; }}
</style>
</head>
<body>
<main>
<header>
<h1>Global Builder Opportunity Briefing</h1>
<p>Generated at {_escape(timestamp)}</p>
<p>Applied filters: {_escape(filters_text)}</p>
<p>Opportunities shown: {len(views)}</p>
<p class="disclaimer">Evidence-based report from the local SQLite ledger. Inclusion is not a
guarantee that an opportunity is valid, funded, or still open — always verify against the
original listing before applying. Values the source did not provide remain
&ldquo;{_escape(UNKNOWN)}&rdquo;.</p>
</header>
{controls}
{body}
<footer>Private local report generated by Global Builder Opportunity Radar (Phase 4A).
No server, no tracking, no external resources.</footer>
</main>
<script>
(function () {{
  var textInput = document.getElementById("filter-text");
  var sourceSelect = document.getElementById("filter-source");
  if (!textInput || !sourceSelect) {{ return; }}
  function applyFilters() {{
    var query = textInput.value.trim().toLowerCase();
    var source = sourceSelect.value;
    var cards = document.querySelectorAll(".card");
    cards.forEach(function (card) {{
      var matchesSource = !source || card.getAttribute("data-source") === source;
      var matchesText = !query || card.textContent.toLowerCase().indexOf(query) !== -1;
      card.hidden = !(matchesSource && matchesText);
    }});
    document.querySelectorAll(".group").forEach(function (group) {{
      var visible = group.querySelectorAll(".card:not([hidden])").length;
      group.hidden = visible === 0;
    }});
  }}
  textInput.addEventListener("input", applyFilters);
  sourceSelect.addEventListener("change", applyFilters);
}})();
</script>
</body>
</html>
"""
