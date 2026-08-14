"""Offline parser tests for the HN freelancer-thread admission unit (Phase 3B)."""

import json
from pathlib import Path

from global_builder_radar.collectors.hackernews import parse_freelancer_thread
from global_builder_radar.models import OpportunityCategory, SourceConfig

FIXTURES = Path(__file__).parent / "fixtures"


def _source(options: dict | None = None) -> SourceConfig:
    return SourceConfig(
        id="hackernews_freelancer",
        collector="hackernews_freelancer",
        category=OpportunityCategory.FREELANCE,
        url="https://hn.algolia.com/api/v1",
        max_items=50,
        timeout_seconds=30,
        options={"allowed_comment_prefixes": ["SEEKING FREELANCER"], **(options or {})},
    )


def _parse(tree: dict, source: SourceConfig):
    return parse_freelancer_thread(tree, source, elapsed_seconds=0.0)


def _sample_tree() -> dict:
    return json.loads((FIXTURES / "hn_freelancer_thread_sample.json").read_text(encoding="utf-8"))


def test_keeps_only_requester_side_comments() -> None:
    result = _parse(_sample_tree(), _source())

    assert result.ok is True
    assert [opportunity.external_id for opportunity in result.opportunities] == [
        "48361270",
        "48362000",
    ]
    first = result.opportunities[0]
    assert first.title == "SEEKING FREELANCER"
    assert first.contact == "projects@example.com"
    assert first.contact_type == "email"
    assert first.compensation_text == "$5,000"
    assert first.remote is True
    assert first.url == "https://news.ycombinator.com/item?id=48361270"
    assert first.raw_payload["thread_id"] == "48358236"


def test_worker_ads_chatter_flagged_and_empty_are_rejected() -> None:
    result = _parse(_sample_tree(), _source())

    rejected_ids = {"48363000", "48364000", "48365000", "48366000"}
    accepted_ids = {opportunity.external_id for opportunity in result.opportunities}
    assert accepted_ids.isdisjoint(rejected_ids)


def test_nested_replies_are_not_collected() -> None:
    result = _parse(_sample_tree(), _source())

    assert "48361500" not in {
        opportunity.external_id for opportunity in result.opportunities
    }


def test_second_requester_post_uses_hn_reply_contact() -> None:
    result = _parse(_sample_tree(), _source())

    second = result.opportunities[1]
    assert second.contact is None
    assert second.contact_type == "hn_reply_or_link"
    assert second.compensation_text == "$80"


def test_thread_without_requesters_reports_truthful_zero() -> None:
    tree = {
        "id": 48749020,
        "children": [
            {"id": 1, "text": "SEEKING WORK | Backend engineer | Remote", "created_at": None},
            {"id": 2, "text": "Some chatter about rates.", "created_at": None},
        ],
    }
    result = _parse(tree, _source())

    assert result.ok is True
    assert result.opportunities == []
    assert "parsed=2" in result.message
    assert "accepted=0" in result.message


def test_empty_thread_reports_truthfully() -> None:
    result = _parse({"id": 1, "children": []}, _source())

    assert result.ok is True
    assert result.opportunities == []
    assert "accepted=0" in result.message


def test_external_ids_remain_stable_across_runs() -> None:
    source = _source()
    first_run = [o.external_id for o in _parse(_sample_tree(), source).opportunities]
    second_run = [o.external_id for o in _parse(_sample_tree(), source).opportunities]
    assert first_run == second_run == ["48361270", "48362000"]
