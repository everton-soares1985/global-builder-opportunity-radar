"""Command-line interface.

Configuration:
- Run with `python -X utf8 -m global_builder_radar` or `builder-radar`.
- All commands are read-only toward source platforms.
"""

from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from typing import Annotated

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
from global_builder_radar.logging_config import configure_logging
from global_builder_radar.pipeline import run_collection
from global_builder_radar.storage import RadarStore

app = typer.Typer(no_args_is_help=True, help="Global Builder Opportunity Radar")
console = Console()


def _store() -> RadarStore:
    store = RadarStore(database_path())
    store.initialize()
    return store


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
) -> None:
    """Display or export ranked opportunities."""
    rows = _store().list_opportunities(
        limit=limit,
        min_score=min_score,
        categories=category,
        sources=source,
        paid_only=paid_only,
        with_contact=with_contact,
        include_traditional=include_traditional,
    )
    normalized = [dict(row) for row in rows]
    if output_format == "table":
        table = Table("#", "Score", "Source", "Category", "Title", "Contact", "Pay", "URL")
        for index, row in enumerate(rows, start=1):
            link = Text("open", style=f"link {row['url']}")
            table.add_row(
                str(index),
                str(row["score"]),
                row["source"],
                row["category"],
                row["title"][:70],
                row["contact"] or row["contact_type"] or "—",
                row["compensation_text"] or "—",
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
            body.append(f"{row['contact'] or row['contact_type'] or '—'}\n\n")
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
