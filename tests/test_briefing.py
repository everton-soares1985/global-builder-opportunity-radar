import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from global_builder_radar.briefing import (
    UNKNOWN,
    filter_views,
    render_briefing,
    row_view,
)
from global_builder_radar.cli import app
from global_builder_radar.models import CollectionResult, Opportunity, OpportunityCategory
from global_builder_radar.storage import RadarStore

NOW = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)


def _row(**overrides) -> dict:
    base = {
        "fingerprint": "fp1",
        "source": "opire_bounties",
        "category": "bounty",
        "title": "Fix parser bug",
        "description": "Resolve the parser crash when the input file is empty.",
        "url": "https://example.com/opp/1",
        "contact_type": "email",
        "contact": "owner@example.com",
        "compensation_text": "$100",
        "compensation_amount_min": 100.0,
        "compensation_amount_max": None,
        "compensation_currency": "USD",
        "compensation_unit": "fixed",
        "published_at": "2026-08-10T00:00:00+00:00",
        "deadline": None,
        "deadline_evidence": None,
        "location": None,
        "remote": True,
        "technologies_json": json.dumps(["python"]),
        "effort_evidence": "About two hours",
        "brazil_eligibility": "unknown",
        "service_domains_json": json.dumps(["programming"]),
        "tags_json": "[]",
        "raw_payload_json": "{}",
        "score": 12.0,
        "status": "new",
        "first_seen_at": "2026-08-10T00:00:00+00:00",
        "last_seen_at": "2026-08-10T00:00:00+00:00",
    }
    base.update(overrides)
    return base


def _render(rows: list[dict], **kwargs) -> str:
    views = [row_view(row, NOW) for row in rows]
    return render_briefing(filter_views(views, **kwargs), generated_at=NOW, **kwargs)


def test_renderer_escapes_hostile_source_text() -> None:
    hostile = _row(
        title='<script>alert("xss")</script>',
        description='"><img src=x onerror=alert(1)> apply now',
        contact="bad@example.com\"><a href=javascript:alert(1)>click</a>",
        source='evil" onmouseover="alert(1)',
    )
    html = _render([hostile])
    assert "<script>alert" not in html
    assert "<img src=x" not in html
    assert 'href="javascript:' not in html
    assert "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;" in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html


def test_unsafe_url_never_becomes_a_link() -> None:
    view = row_view(_row(url="javascript:alert(1)"), NOW)
    card = render_briefing([view], generated_at=NOW)
    assert "javascript:" not in card
    assert f'href="{UNKNOWN}' not in card
    assert f"{UNKNOWN} original URL" in card


def test_card_renders_required_evidence() -> None:
    html = _render([_row(deadline="2026-09-01T00:00:00+00:00", location="Remote - global")])
    for expected in (
        "Fix parser bug",
        "opire_bounties",
        "bounty",
        "programming",
        "12.0",
        "$100",
        "2026-09-01T00:00:00+00:00",
        "unknown",
        "Remote - global",
        "python",
        "About two hours",
        "owner@example.com",
        "Why it surfaced",
        "Next action",
        "Open original opportunity",
        "https://example.com/opp/1",
    ):
        assert expected in html
    assert 'target="_blank" rel="noopener noreferrer"' in html
    assert "Generated at 2026-08-15" in html
    assert "evidence-based" in html.lower()


def test_unknown_values_render_honestly() -> None:
    bare = _row(
        compensation_text=None,
        contact=None,
        contact_type=None,
        technologies_json="[]",
        service_domains_json="[]",
        effort_evidence=None,
        deadline=None,
        published_at=None,
        first_seen_at=None,
        description="",
        score=None,
    )
    html = _render([bare])
    assert html.count(UNKNOWN) >= 5
    assert "Stored pay evidence" not in html
    assert "Service domains matched" not in html
    assert "Listed by an enabled alternative-income source." in html


def test_grouping_is_factual() -> None:
    ready = _row(fingerprint="ready", title="Paid gig", url="https://example.com/ready")
    needs = _row(
        fingerprint="needs",
        title="No pay evidence",
        url="https://example.com/needs",
        compensation_text=None,
    )
    blocked = _row(
        fingerprint="blocked",
        title="Not in Brazil",
        url="https://example.com/blocked",
        brazil_eligibility="ineligible",
    )
    views = [row_view(row, NOW) for row in (ready, needs, blocked)]
    assert [view["group"] for view in views] == ["ready", "needs_details", "brazil_unavailable"]
    html = render_briefing(views, generated_at=NOW)
    ready_pos = html.index("Ready to review")
    needs_pos = html.index("Needs details")
    blocked_pos = html.index("Brazil unavailable")
    assert ready_pos < needs_pos < blocked_pos
    assert all(title in html for title in ("Paid gig", "No pay evidence", "Not in Brazil"))


def test_filters_are_factual() -> None:
    paid_fresh = _row(fingerprint="a", url="https://example.com/a")
    unpaid = _row(
        fingerprint="b", url="https://example.com/b", compensation_text=None, score=5.0
    )
    stale = _row(
        fingerprint="c",
        url="https://example.com/c",
        published_at="2026-06-01T00:00:00+00:00",
        first_seen_at="2026-06-01T00:00:00+00:00",
    )
    undated = _row(
        fingerprint="d", url="https://example.com/d", published_at=None, first_seen_at=None
    )
    views = [row_view(row, NOW) for row in (paid_fresh, unpaid, stale, undated)]

    def titles(selected: list[dict]) -> set[str]:
        return {view["title"] for view in selected}

    assert len(filter_views(views, limit=0)) == 4
    assert titles(filter_views(views, paid_only=True)) == {"Fix parser bug"}
    assert titles(filter_views(views, min_score=10)) == {"Fix parser bug"}
    assert titles(filter_views(views, max_age_days=30)) == {"Fix parser bug"}
    assert len(filter_views(views, limit=2)) == 2


def _seed_ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "radar.sqlite3"
    monkeypatch.setenv("GBR_DATABASE_PATH", str(path))
    store = RadarStore(path)
    store.initialize()
    enabled = Opportunity(
        source="opire_bounties",
        category=OpportunityCategory.BOUNTY,
        external_id="1",
        title="Enabled bounty",
        url="https://example.com/enabled",
        compensation_text="$250",
        score=10,
    )
    retired = Opportunity(
        source="algora_bounties",
        category=OpportunityCategory.BOUNTY,
        external_id="2",
        title="Retired source bounty",
        url="https://example.com/retired",
        compensation_text="$999",
        score=50,
    )
    store.record_result(CollectionResult(source="opire_bounties", opportunities=[enabled]))
    store.record_result(CollectionResult(source="algora_bounties", opportunities=[retired]))
    return path


def _ledger_snapshot(path: Path):
    connection = sqlite3.connect(path)
    try:
        opportunities = connection.execute(
            "SELECT * FROM opportunities ORDER BY fingerprint"
        ).fetchall()
        runs = connection.execute("SELECT * FROM collection_runs ORDER BY id").fetchall()
    finally:
        connection.close()
    return opportunities, runs


def test_briefing_hides_disabled_sources_by_default(tmp_path: Path, monkeypatch) -> None:
    _seed_ledger(tmp_path, monkeypatch)
    output = tmp_path / "briefing.html"
    result = CliRunner().invoke(app, ["briefing", "--output", str(output)])
    assert result.exit_code == 0
    html = output.read_text(encoding="utf-8")
    assert "Enabled bounty" in html
    assert "Retired source bounty" not in html
    assert "$999" not in html
    assert "1 card(s)" in " ".join(result.output.split())


def test_briefing_does_not_mutate_ledger(tmp_path: Path, monkeypatch) -> None:
    path = _seed_ledger(tmp_path, monkeypatch)
    before = _ledger_snapshot(path)
    result = CliRunner().invoke(
        app, ["briefing", "--output", str(tmp_path / "briefing.html"), "--paid-only"]
    )
    assert result.exit_code == 0
    assert _ledger_snapshot(path) == before


def test_briefing_filters_report_truthful_counts(tmp_path: Path, monkeypatch) -> None:
    _seed_ledger(tmp_path, monkeypatch)
    result = CliRunner().invoke(
        app,
        [
            "briefing",
            "--output",
            str(tmp_path / "briefing.html"),
            "--min-score",
            "100",
        ],
    )
    assert result.exit_code == 0
    assert "0 card(s)" in " ".join(result.output.split())
    html = (tmp_path / "briefing.html").read_text(encoding="utf-8")
    assert "No eligible opportunities match the current filters." in html
