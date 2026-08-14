"""Offline tests for the Superteam-style listing collector parsing.

The fixture mirrors the Superteam Earn card structure (listing anchors with a
title paragraph and type/amount hints). Tests never touch the network: the
page is parsed locally with Scrapling's Adaptor, exactly like the collector
parses a fetched page.
"""

from pathlib import Path

from scrapling.parser import Adaptor

from global_builder_radar.collectors.scrapling_links import parse_listing_page
from global_builder_radar.models import SourceConfig

FIXTURE = Path(__file__).parent / "fixtures" / "superteam_listing_sample.html"


def _source(**overrides) -> SourceConfig:
    base = dict(
        id="superteam_earn",
        collector="scrapling_links",
        category="mixed",
        url="https://superteam.fun/earn/all?tab=bounties",
        max_items=50,
        timeout_seconds=45,
        options={
            "fetcher": "dynamic",
            "link_pattern": "/earn/listing/",
            "title_selector": "p.line-clamp-1::text",
        },
    )
    base.update(overrides)
    return SourceConfig(**base)


def _parse(html: str, source: SourceConfig | None = None):
    page = Adaptor(html, url="https://superteam.fun")
    return parse_listing_page(page, source or _source(), elapsed_seconds=0.1)


def test_listing_cards_are_normalized_and_deduplicated():
    result = _parse(FIXTURE.read_text(encoding="utf-8"))
    assert result.ok is True
    assert result.message == "links_matched=3 pattern='/earn/listing/'"
    urls = [op.url for op in result.opportunities]
    assert urls == [
        "https://superteam.fun/earn/listing/example-bounty-1",
        "https://superteam.fun/earn/listing/example-hackathon",
        "https://superteam.fun/earn/listing/example-grant",
    ]


def test_titles_come_from_the_configured_selector():
    result = _parse(FIXTURE.read_text(encoding="utf-8"))
    titles = [op.title for op in result.opportunities]
    assert titles == [
        "Build a Solana Analytics Dashboard",
        "Radar Hackathon 2026",
        "Open Source Grant Round",
    ]


def test_individual_payment_is_captured_and_prize_pool_is_not():
    result = _parse(FIXTURE.read_text(encoding="utf-8"))
    bounty, hackathon, grant = result.opportunities
    assert bounty.compensation_text == "$1,500"
    # Aggregate prize pools are not individual pay; keep the field empty.
    assert hackathon.compensation_text is None
    assert grant.compensation_text is None


def test_opportunity_kind_hints_survive_in_description():
    result = _parse(FIXTURE.read_text(encoding="utf-8"))
    hints = [op.description for op in result.opportunities]
    assert "Bounty" in hints[0]
    assert "Hackathon" in hints[1]
    assert "Grant" in hints[2]


def test_non_listing_links_are_rejected():
    result = _parse(FIXTURE.read_text(encoding="utf-8"))
    assert all("/earn/listing/" in op.url for op in result.opportunities)
    assert not any("Navigation link" in op.description for op in result.opportunities)


def test_empty_page_fails_truthfully():
    result = _parse("<html><body><p>No listings</p></body></html>")
    assert result.ok is False
    assert result.opportunities == []
    assert result.message == "links_matched=0 pattern='/earn/listing/'"


def test_max_items_caps_collection():
    result = _parse(FIXTURE.read_text(encoding="utf-8"), _source(max_items=2))
    assert result.ok is True
    assert len(result.opportunities) == 2
