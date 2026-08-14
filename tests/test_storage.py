import sqlite3
from pathlib import Path

from global_builder_radar.models import (
    CollectionResult,
    Opportunity,
    OpportunityCategory,
    OpportunityStatus,
)
from global_builder_radar.storage import RadarStore


def test_store_upserts_duplicate_fingerprint(tmp_path: Path) -> None:
    store = RadarStore(tmp_path / "radar.sqlite3")
    store.initialize()
    opportunity = Opportunity(
        source="test",
        category=OpportunityCategory.BOUNTY,
        external_id="same",
        title="Original",
        url="https://example.com/1",
    )
    first_result = CollectionResult(source="test", opportunities=[opportunity])
    assert store.record_result(first_result) == (1, 0)
    opportunity.title = "Updated"
    updated_result = CollectionResult(source="test", opportunities=[opportunity])
    assert store.record_result(updated_result) == (0, 1)
    rows = store.list_opportunities()
    assert len(rows) == 1
    assert rows[0]["title"] == "Updated"


def test_store_filters_paid_category_and_contact(tmp_path: Path) -> None:
    store = RadarStore(tmp_path / "radar.sqlite3")
    store.initialize()
    paid = Opportunity(
        source="opire",
        category=OpportunityCategory.BOUNTY,
        external_id="paid",
        title="Paid bounty",
        url="https://example.com/paid",
        contact="owner@example.com",
        contact_type="email",
        compensation_text="$100",
        score=20,
    )
    unpaid = Opportunity(
        source="hn",
        category=OpportunityCategory.DIRECT_JOB,
        external_id="unpaid",
        title="Unknown salary",
        url="https://example.com/unknown",
        score=30,
    )
    store.record_result(CollectionResult(source="mixed", opportunities=[paid, unpaid]))
    rows = store.list_opportunities(
        categories=["bounty"], paid_only=True, with_contact=True
    )
    assert [row["title"] for row in rows] == ["Paid bounty"]


def test_store_hides_discarded_opportunities(tmp_path: Path) -> None:
    store = RadarStore(tmp_path / "radar.sqlite3")
    store.initialize()
    opportunity = Opportunity(
        source="test",
        category=OpportunityCategory.BOUNTY,
        external_id="spam",
        title="Keyword-stuffed bounty",
        url="https://example.com/spam",
        status=OpportunityStatus.DISCARDED,
    )
    store.record_result(CollectionResult(source="test", opportunities=[opportunity]))
    assert store.list_opportunities() == []


def test_store_hides_traditional_jobs_by_default(tmp_path: Path) -> None:
    store = RadarStore(tmp_path / "radar.sqlite3")
    store.initialize()
    opportunity = Opportunity(
        source="legacy_jobs",
        category=OpportunityCategory.DIRECT_JOB,
        external_id="job",
        title="Permanent full-time role",
        url="https://example.com/job",
    )
    store.record_result(CollectionResult(source="legacy_jobs", opportunities=[opportunity]))

    assert store.list_opportunities() == []
    assert len(store.list_opportunities(include_traditional=True)) == 1


def test_store_hides_classified_traditional_jobs_by_default(tmp_path: Path) -> None:
    store = RadarStore(tmp_path / "radar.sqlite3")
    store.initialize()
    opportunity = Opportunity(
        source="mixed_source",
        category=OpportunityCategory.TRADITIONAL_JOB,
        external_id="classified-job",
        title="Classified permanent role",
        url="https://example.com/classified",
    )
    store.record_result(CollectionResult(source="mixed_source", opportunities=[opportunity]))

    assert store.list_opportunities() == []
    assert len(store.list_opportunities(include_traditional=True)) == 1


def test_initialize_migrates_legacy_schema(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(legacy) as connection:
        connection.execute(
            """
            CREATE TABLE opportunities (
                fingerprint TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                category TEXT NOT NULL,
                external_id TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                url TEXT NOT NULL,
                contact_type TEXT,
                contact TEXT,
                compensation_text TEXT,
                published_at TEXT,
                deadline TEXT,
                location TEXT,
                remote INTEGER,
                tags_json TEXT NOT NULL,
                raw_payload_json TEXT NOT NULL,
                score REAL NOT NULL,
                status TEXT NOT NULL,
                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            "INSERT INTO opportunities (fingerprint, source, category, title, description, "
            "url, tags_json, raw_payload_json, score, status) "
            "VALUES ('f1', 'legacy', 'bounty', 'Old row', '', 'https://example.com/old', "
            "'[]', '{}', 5, 'new')"
        )

    store = RadarStore(legacy)
    store.initialize()

    with sqlite3.connect(legacy) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(opportunities)")}
        preserved = connection.execute(
            "SELECT title FROM opportunities WHERE fingerprint = 'f1'"
        ).fetchone()
    assert "compensation_amount_min" in columns
    assert "brazil_eligibility" in columns
    assert "technologies_json" in columns
    assert preserved[0] == "Old row"
