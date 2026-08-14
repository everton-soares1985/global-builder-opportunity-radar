"""Offline parser tests for the Reddit RSS admission unit (Phase 3A)."""

from pathlib import Path

import feedparser

from global_builder_radar.collectors.reddit import parse_reddit_feed
from global_builder_radar.models import OpportunityCategory, SourceConfig

FIXTURES = Path(__file__).parent / "fixtures"

EMPTY_FEED = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<feed xmlns="http://www.w3.org/2005/Atom">'
    "<title>empty</title>"
    "</feed>"
)


def _source(source_id: str, options: dict) -> SourceConfig:
    return SourceConfig(
        id=source_id,
        collector="reddit_rss",
        category=OpportunityCategory.FREELANCE,
        url=f"https://www.reddit.com/r/{source_id.removeprefix('reddit_')}/new/.rss",
        max_items=50,
        timeout_seconds=30,
        options=options,
    )


def _parse(fixture_path: Path, source: SourceConfig):
    feed = feedparser.parse(fixture_path.read_bytes())
    return parse_reddit_feed(feed, source, elapsed_seconds=0.0)


def test_jobbit_keeps_only_requester_side_posts() -> None:
    source = _source("reddit_jobbit", {"allowed_title_prefixes": ["[Hiring]"]})
    result = _parse(FIXTURES / "reddit_jobbit_sample.xml", source)

    assert result.ok is True
    titles = [opportunity.title for opportunity in result.opportunities]
    assert titles == [
        "[HIRING] Python automation contractor for CRM rollout [$50/hr]",
        "[Hiring] Freelance data pipeline builder ($2,000 fixed)",
    ]
    first = result.opportunities[0]
    assert first.external_id == "t3_exjobbit1"
    assert first.compensation_text == "$50"
    assert first.contact == "jobs@example.com"
    assert first.contact_type == "email"


def test_slavelabour_keeps_only_paid_task_requests() -> None:
    source = _source("reddit_slavelabour", {"allowed_title_prefixes": ["[TASK]"]})
    result = _parse(FIXTURES / "reddit_slavelabour_sample.xml", source)

    assert result.ok is True
    titles = [opportunity.title for opportunity in result.opportunities]
    assert titles == [
        "[TASK] Build a Python web scraper for product prices - $40",
        "[Task] Rename 3,000 pictures to match displayed names for $20",
    ]
    lowered = [title.lower() for title in titles]
    assert not any(title.startswith("[offer]") for title in lowered)
    assert not any(title.startswith("[mod post]") for title in lowered)


def test_legacy_single_prefix_option_still_supported() -> None:
    source = _source("reddit_forhire", {"required_flair_prefix": "[Hiring]"})
    result = _parse(FIXTURES / "reddit_jobbit_sample.xml", source)
    assert len(result.opportunities) == 2


def test_empty_feed_reports_truthfully() -> None:
    source = _source("reddit_jobbit", {"allowed_title_prefixes": ["[Hiring]"]})
    result = parse_reddit_feed(feedparser.parse(EMPTY_FEED), source, 0.0)
    assert result.ok is True
    assert result.opportunities == []
    assert result.message == "parsed=0 accepted=0"


def test_malformed_xml_body_fails_truthfully() -> None:
    source = _source("reddit_slavelabour", {"allowed_title_prefixes": ["[TASK]"]})
    feed = feedparser.parse((FIXTURES / "reddit_malformed_body.xml").read_bytes())
    result = parse_reddit_feed(feed, source, 0.0)
    assert result.ok is False
    assert result.opportunities == []
    assert "feed_parse_failed" in result.message
    assert "malformed_feed_body" in result.message


def test_html_block_page_fails_truthfully() -> None:
    source = _source("reddit_slavelabour", {"allowed_title_prefixes": ["[TASK]"]})
    feed = feedparser.parse((FIXTURES / "reddit_blocked_body.html").read_bytes())
    result = parse_reddit_feed(feed, source, 0.0)
    assert result.ok is False
    assert result.opportunities == []
    assert "non_feed_body" in result.message


def test_external_ids_remain_stable_across_runs() -> None:
    source = _source("reddit_jobbit", {"allowed_title_prefixes": ["[Hiring]"]})
    fixture = FIXTURES / "reddit_jobbit_sample.xml"
    first_run = [o.external_id for o in _parse(fixture, source).opportunities]
    second_run = [o.external_id for o in _parse(fixture, source).opportunities]
    assert first_run == second_run == ["t3_exjobbit1", "t3_exjobbit2"]
