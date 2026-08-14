"""Command-line interface.

Configuration:
- Run with `python -X utf8 -m global_builder_radar` or `builder-radar`.
- All commands are read-only toward source platforms.
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from global_builder_radar.config import (
    database_path,
    load_profile_rules,
    load_radar_config,
)
from global_builder_radar.github_issues import github_issue_api_url, verdict_from_payload
from global_builder_radar.logging_config import configure_logging
from global_builder_radar.pipeline import run_collection
from global_builder_radar.scoring import basic_quality, freshness_days
from global_builder_radar.storage import RadarStore

app = typer.Typer(no_args_is_help=True, help="Global Builder Opportunity Radar")
console = Console()


def _store() -> RadarStore:
    store = RadarStore(database_path())
    store.initialize()
    return store


def _row_domains(row: dict) -> list[str]:
    try:
        return json.loads(row.get("service_domains_json") or "[]")
    except json.JSONDecodeError:
        return []


def _row_signals(row: dict) -> tuple[int | None, float]:
    """Basic freshness (days) and quality (0-1) for a stored row."""

    now = datetime.now(UTC)
    age = freshness_days(row.get("published_at"), now)
    if age is None:
        age = freshness_days(row.get("first_seen_at"), now)
    quality = basic_quality(
        row.get("compensation_text"),
        row.get("description") or "",
        row.get("contact"),
        bool(row.get("published_at") or row.get("deadline")),
    )
    return age, quality


@app.command("init-db")
def init_db() -> None:
    """Initialize the local SQLite database."""
    configure_logging()
    store = _store()
    console.print(f"Database ready: {store.path}")


@app.command()
def sources() -> None:
    """Show the configured source catalog."""
    config = load_radar_config()
    table = Table("Source", "Collector", "Category", "Enabled", "URL")
    for source in config.sources:
        table.add_row(
            source.id,
            source.collector,
            source.category.value,
            "yes" if source.enabled else "no",
            source.url,
        )
    console.print(table)


@app.command()
def collect(
    source: Annotated[
        list[str] | None,
        typer.Option("--source", "-s", help="Source id; repeat to select multiple."),
    ] = None,
) -> None:
    """Collect enabled sources and persist normalized opportunities."""
    configure_logging()
    config = load_radar_config()
    selected = [item for item in config.sources if item.enabled]
    if source:
        requested = set(source)
        selected = [item for item in selected if item.id in requested]
        missing = requested - {item.id for item in selected}
        if missing:
            raise typer.BadParameter(f"Unknown or disabled sources: {', '.join(sorted(missing))}")
    if not selected:
        raise typer.BadParameter("No enabled sources selected")
    store = _store()
    results = asyncio.run(run_collection(selected, load_profile_rules(), store))
    table = Table("Source", "Status", "Items", "Seconds", "Message")
    for result in results:
        table.add_row(
            result.source,
            "OK" if result.ok else "FAILED",
            str(len(result.opportunities)),
            f"{result.elapsed_seconds:.2f}",
            result.message,
        )
    console.print(table)


@app.command()
def report(
    limit: Annotated[int, typer.Option(min=1, max=500)] = 30,
    min_score: Annotated[float, typer.Option()] = 0,
    output_format: Annotated[str, typer.Option("--format")] = "table",
    output: Annotated[Path | None, typer.Option()] = None,
    category: Annotated[
        list[str] | None, typer.Option("--category", "-c", help="Repeat to select categories.")
    ] = None,
    source: Annotated[
        list[str] | None, typer.Option("--source", "-s", help="Repeat to select sources.")
    ] = None,
    paid_only: Annotated[bool, typer.Option("--paid-only")] = False,
    with_contact: Annotated[bool, typer.Option("--with-contact")] = False,
    include_traditional: Annotated[
        bool,
        typer.Option(
            "--include-traditional",
            help="Include legacy traditional-job records for audit purposes.",
        ),
    ] = False,
    include_disabled_sources: Annotated[
        bool,
        typer.Option(
            "--include-disabled-sources",
            help="Include records from retired/disabled sources (audit only).",
        ),
    ] = False,
) -> None:
    """Display or export ranked opportunities."""
    config = load_radar_config()
    enabled = (
        [source.id for source in config.sources if source.enabled]
        if not include_disabled_sources
        else None
    )
    rows = _store().list_opportunities(
        limit=limit,
        min_score=min_score,
        categories=category,
        sources=source,
        enabled_sources=enabled,
        paid_only=paid_only,
        with_contact=with_contact,
        include_traditional=include_traditional,
    )
    normalized = [dict(row) for row in rows]
    for row in normalized:
        age, quality = _row_signals(row)
        row["service_domains"] = _row_domains(row)
        row["freshness_days"] = age
        row["quality_score"] = quality
    if output_format == "table":
        table = Table(
            "#", "Score", "Source", "Category", "Domains", "Title", "Contact", "Pay",
            "Age d", "Quality", "URL",
        )
        for index, row in enumerate(rows, start=1):
            link = Text("open", style=f"link {row['url']}")
            age, quality = _row_signals(dict(row))
            table.add_row(
                str(index),
                str(row["score"]),
                row["source"],
                row["category"],
                ", ".join(_row_domains(dict(row))) or "—",
                row["title"][:70],
                row["contact"] or row["contact_type"] or "—",
                row["compensation_text"] or "—",
                str(age) if age is not None else "—",
                f"{quality:.2f}",
                link,
            )
        console.print(table)
        return
    if output_format == "detailed":
        for index, row in enumerate(rows, start=1):
            description = " ".join(row["description"].split())
            if len(description) > 1_200:
                description = f"{description[:1_197]}..."
            body = Text()
            body.append("Score: ", style="bold")
            body.append(f"{row['score']}  ")
            body.append("Type: ", style="bold")
            body.append(f"{row['category']}  ")
            body.append("Source: ", style="bold")
            body.append(f"{row['source']}\n")
            body.append("Pay: ", style="bold")
            body.append(f"{row['compensation_text'] or '—'}  ")
            body.append("Contact: ", style="bold")
            body.append(f"{row['contact'] or row['contact_type'] or '—'}\n")
            age, quality = _row_signals(dict(row))
            body.append("Domains: ", style="bold")
            body.append(f"{', '.join(_row_domains(dict(row))) or 'unknown'}  ")
            body.append("Age: ", style="bold")
            body.append(f"{age if age is not None else '—'}d  ")
            body.append("Quality: ", style="bold")
            body.append(f"{quality:.2f}\n\n")
            body.append(f"{description or 'No description provided.'}\n\n")
            body.append(row["url"], style=f"link {row['url']}")
            console.print(Panel(body, title=Text(f"{index}. {row['title']}"), border_style="blue"))
        return
    if output_format not in {"json", "csv"}:
        raise typer.BadParameter("--format must be table, detailed, json, or csv")
    if output is None:
        output = Path("reports") / f"opportunities.{output_format}"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "json":
        output.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        with output.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(normalized[0]) if normalized else [])
            if normalized:
                writer.writeheader()
                writer.writerows(normalized)
    console.print(f"Exported {len(normalized)} opportunities to {output}")


@app.command("verify-github-issues")
def verify_github_issues() -> None:
    """Check ledger GitHub issues and hide closed, zero-bounty, or dead ones.

    Read-only toward GitHub. Closed and dead-reference rows become
    status='discarded' and open zero-bounty rows lose their pay fields;
    everything stays in SQLite.
    """
    configure_logging()
    store = _store()
    rows = store.github_issue_rows()
    discarded = cleared = checked = errors = 0
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "global-builder-opportunity-radar",
    }
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    with httpx.Client(timeout=15, headers=headers, follow_redirects=True) as client:
        for row in rows:
            api_url = github_issue_api_url(row["url"])
            if not api_url:
                continue
            try:
                response = client.get(api_url)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in {403, 429}:
                    # Rate limit: stop the batch instead of repeating failures.
                    message = "GitHub rate limit reached — batch stopped"
                    reset = exc.response.headers.get("X-RateLimit-Reset")
                    if reset and reset.isdigit():
                        reset_at = datetime.fromtimestamp(int(reset), tz=UTC).astimezone()
                        message += f"; limit resets at {reset_at:%Y-%m-%d %H:%M} local time"
                    console.print(f"[yellow]{message}.[/yellow]")
                    break
                if exc.response.status_code in {404, 410}:
                    # Repository or issue no longer exists: dead reference.
                    store.discard(row["fingerprint"])
                    discarded += 1
                    console.print(
                        f"[red]dead     [/red] {row['url']} (HTTP {exc.response.status_code})"
                    )
                else:
                    errors += 1
                    console.print(
                        f"[yellow]skipped {row['url']} (HTTP {exc.response.status_code})[/yellow]"
                    )
                continue
            except httpx.HTTPError as exc:
                errors += 1
                console.print(f"[yellow]skipped {row['url']} ({type(exc).__name__})[/yellow]")
                continue
            checked += 1
            closed, zero_bounty = verdict_from_payload(response.json())
            if closed:
                store.discard(row["fingerprint"])
                discarded += 1
                console.print(f"[red]closed   [/red] {row['url']}")
            elif zero_bounty:
                store.clear_compensation(row["fingerprint"])
                cleared += 1
                console.print(f"[yellow]no pay  [/yellow] {row['url']}")
    console.print(
        f"Checked {checked}/{len(rows)} GitHub issues: "
        f"{discarded} hidden (closed or dead), {cleared} pay cleared (zero-bounty), "
        f"{errors} skipped on error."
    )


@app.command()
def health() -> None:
    """Show the most recent run for each source."""
    rows = _store().source_health()
    table = Table("Source", "Status", "Items", "Seconds", "Started", "Message")
    for row in rows:
        table.add_row(
            row["source"],
            "OK" if row["ok"] else "FAILED",
            str(row["item_count"]),
            f"{row['elapsed_seconds']:.2f}",
            row["started_at"],
            row["message"],
        )
    console.print(table)
