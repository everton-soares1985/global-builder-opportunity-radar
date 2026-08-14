"""SQLite persistence and deduplication.

Configuration:
- GBR_DATABASE_PATH overrides the default data/radar.sqlite3 path.
- WAL mode allows concurrent readers during collection.
- Schema migrations add columns only, keeping existing ledgers readable.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path

from global_builder_radar.models import CollectionResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ok INTEGER NOT NULL,
    message TEXT NOT NULL,
    elapsed_seconds REAL NOT NULL,
    item_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS opportunities (
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
    compensation_amount_min REAL,
    compensation_amount_max REAL,
    compensation_currency TEXT,
    compensation_unit TEXT,
    published_at TEXT,
    deadline TEXT,
    deadline_evidence TEXT,
    location TEXT,
    remote INTEGER,
    technologies_json TEXT NOT NULL DEFAULT '[]',
    effort_evidence TEXT,
    brazil_eligibility TEXT NOT NULL DEFAULT 'unknown',
    service_domains_json TEXT NOT NULL DEFAULT '[]',
    tags_json TEXT NOT NULL,
    raw_payload_json TEXT NOT NULL,
    score REAL NOT NULL,
    status TEXT NOT NULL,
    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_opportunities_score ON opportunities(score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_source ON opportunities(source);
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
"""

_COLUMN_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("compensation_amount_min", "REAL"),
    ("compensation_amount_max", "REAL"),
    ("compensation_currency", "TEXT"),
    ("compensation_unit", "TEXT"),
    ("deadline_evidence", "TEXT"),
    ("technologies_json", "TEXT NOT NULL DEFAULT '[]'"),
    ("effort_evidence", "TEXT"),
    ("brazil_eligibility", "TEXT NOT NULL DEFAULT 'unknown'"),
    ("service_domains_json", "TEXT NOT NULL DEFAULT '[]'"),
)


class RadarStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            existing = {
                row[1] for row in connection.execute("PRAGMA table_info(opportunities)")
            }
            for column, column_type in _COLUMN_MIGRATIONS:
                if column not in existing:
                    connection.execute(
                        f"ALTER TABLE opportunities ADD COLUMN {column} {column_type}"
                    )

    def record_result(self, result: CollectionResult) -> tuple[int, int]:
        inserted = 0
        updated = 0
        with self.connect() as connection:
            for opportunity in result.opportunities:
                exists = connection.execute(
                    "SELECT 1 FROM opportunities WHERE fingerprint = ?",
                    (opportunity.fingerprint,),
                ).fetchone()
                connection.execute(
                    """
                    INSERT INTO opportunities (
                        fingerprint, source, category, external_id, title, description, url,
                        contact_type, contact, compensation_text, compensation_amount_min,
                        compensation_amount_max, compensation_currency, compensation_unit,
                        published_at, deadline, deadline_evidence, location, remote,
                        technologies_json, effort_evidence, brazil_eligibility,
                        service_domains_json, tags_json,
                        raw_payload_json, score, status
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?
                    )
                    ON CONFLICT(fingerprint) DO UPDATE SET
                        title = excluded.title,
                        description = excluded.description,
                        url = excluded.url,
                        contact_type = excluded.contact_type,
                        contact = excluded.contact,
                        compensation_text = excluded.compensation_text,
                        compensation_amount_min = excluded.compensation_amount_min,
                        compensation_amount_max = excluded.compensation_amount_max,
                        compensation_currency = excluded.compensation_currency,
                        compensation_unit = excluded.compensation_unit,
                        published_at = excluded.published_at,
                        deadline = excluded.deadline,
                        deadline_evidence = excluded.deadline_evidence,
                        location = excluded.location,
                        remote = excluded.remote,
                        technologies_json = excluded.technologies_json,
                        effort_evidence = excluded.effort_evidence,
                        brazil_eligibility = excluded.brazil_eligibility,
                        service_domains_json = excluded.service_domains_json,
                        tags_json = excluded.tags_json,
                        raw_payload_json = excluded.raw_payload_json,
                        score = excluded.score,
                        status = excluded.status,
                        last_seen_at = CURRENT_TIMESTAMP
                    """,
                    (
                        opportunity.fingerprint,
                        opportunity.source,
                        opportunity.category.value,
                        opportunity.external_id,
                        opportunity.title,
                        opportunity.description,
                        opportunity.url,
                        opportunity.contact_type,
                        opportunity.contact,
                        opportunity.compensation_text,
                        opportunity.compensation_amount_min,
                        opportunity.compensation_amount_max,
                        opportunity.compensation_currency,
                        opportunity.compensation_unit,
                        opportunity.published_at.isoformat() if opportunity.published_at else None,
                        opportunity.deadline.isoformat() if opportunity.deadline else None,
                        opportunity.deadline_evidence,
                        opportunity.location,
                        opportunity.remote,
                        json.dumps(opportunity.technologies, ensure_ascii=False),
                        opportunity.effort_evidence,
                        opportunity.brazil_eligibility.value,
                        json.dumps(opportunity.service_domains, ensure_ascii=False),
                        json.dumps(opportunity.tags, ensure_ascii=False),
                        opportunity.raw_payload_json(),
                        opportunity.score,
                        opportunity.status.value,
                    ),
                )
                if exists:
                    updated += 1
                else:
                    inserted += 1
            connection.execute(
                """
                INSERT INTO collection_runs (source, ok, message, elapsed_seconds, item_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    result.source,
                    result.ok,
                    result.message,
                    result.elapsed_seconds,
                    len(result.opportunities),
                ),
            )
        return inserted, updated

    def list_opportunities(
        self,
        limit: int = 50,
        min_score: float = 0,
        categories: list[str] | None = None,
        sources: list[str] | None = None,
        paid_only: bool = False,
        with_contact: bool = False,
        include_traditional: bool = False,
    ) -> list[sqlite3.Row]:
        clauses = ["score >= ?", "status != 'discarded'"]
        parameters: list[object] = [min_score]
        if not include_traditional:
            clauses.append("category NOT IN ('direct_job', 'traditional_job')")
        if categories:
            placeholders = ", ".join("?" for _ in categories)
            clauses.append(f"category IN ({placeholders})")
            parameters.extend(categories)
        if sources:
            placeholders = ", ".join("?" for _ in sources)
            clauses.append(f"source IN ({placeholders})")
            parameters.extend(sources)
        if paid_only:
            clauses.append("compensation_text IS NOT NULL")
        if with_contact:
            clauses.append("contact IS NOT NULL")
        parameters.append(limit)
        with self.connect() as connection:
            return list(
                connection.execute(
                    f"""
                    SELECT * FROM opportunities
                    WHERE {" AND ".join(clauses)}
                    ORDER BY score DESC, COALESCE(published_at, first_seen_at) DESC
                    LIMIT ?
                    """,
                    parameters,
                ).fetchall()
            )

    def source_health(self) -> Iterable[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    """
                    SELECT r.*
                    FROM collection_runs r
                    JOIN (
                        SELECT source, MAX(id) AS max_id FROM collection_runs GROUP BY source
                    ) latest ON latest.max_id = r.id
                    ORDER BY r.source
                    """
                ).fetchall()
            )
