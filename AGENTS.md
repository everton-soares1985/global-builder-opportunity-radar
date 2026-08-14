# Agent operating contract

This file is the mandatory operating contract for every coding agent working in this repository.
The canonical product knowledge lives in `docs/`; IDE Wiki/Knowledge cards are derived indexes,
not replacements for versioned documentation.

## Product mission

Build a reliable radar for **alternative income opportunities outside traditional employment**:

- freelance work;
- fixed-scope paid projects and contracts;
- open-source bounties;
- grants and paid fellowships;
- prize-bearing hackathons and competitions;
- paid ambassador, contributor, and builder programs.

Traditional full-time or permanent job aggregation is out of scope. Wellfound and InfoJobs already
serve that purpose. A source that mixes jobs with projects may be enabled only when its collector
can exclude ordinary employment reliably.

Read [`docs/mission.md`](docs/mission.md) before changing product scope or ranking.

## Mandatory reading order

Before editing code in a new session, read these files in order:

1. `AGENTS.md`
2. `docs/mission.md`
3. `docs/architecture.md`
4. `docs/module-map.md`
5. `docs/source-admission.md`
6. `docs/roadmap.md`
7. `docs/review-findings.md`
8. `docs/current-work.md`
9. the documentation and tests related to the module being changed

Do not infer current behavior from chat history. The repository is the source of truth.

## Autonomous execution loop

1. Inspect `git status`, the current branch, and the latest test state.
2. Resolve every open blocking item in `docs/review-findings.md` before selecting new roadmap work.
3. Select the first incomplete roadmap item whose prerequisites are complete.
4. Read `docs/current-work.md` and use its current work unit as the bounded implementation plan.
5. Implement only that roadmap item; do not redesign unrelated modules.
6. Add or update deterministic offline tests.
7. Run the validation commands defined below.
8. Update `docs/roadmap.md`, `docs/module-map.md`, `docs/sources.md`, and `CHANGELOG.md` when the
   delivered behavior changes them.
9. If IDE Wiki/Knowledge is available, create or update the corresponding knowledge cards from the
   canonical docs. If it is unavailable, record that fact in the session report and continue.
10. Stop only when the selected phase meets every acceptance criterion or has a documented blocker.
11. Never commit, push, deploy, send messages, or incur paid external usage without explicit user
    authorization.

When one phase finishes with all gates green, the agent may continue to the next roadmap phase if
the user's instruction explicitly requests autonomous continuation. It must still preserve one
phase per diff and report the boundary between phases.

## Architecture invariants

- Collectors acquire one source and return normalized `Opportunity` objects.
- Collectors never write directly to SQLite, score records, send outreach, or invoke other
  collectors.
- The pipeline isolates source failures. One broken source must not stop the others.
- The domain model remains source-agnostic; source-only evidence belongs in `raw_payload`.
- SQLite is the canonical local ledger. Sheets, dashboards, and alerts are projections.
- Deterministic validation and scoring remain available even after AI classification is added.
- Never report fabricated collection success or invented compensation, eligibility, deadlines, or
  contacts.
- Preserve provenance: every actionable record needs a public source URL and collection evidence.
- Prefer official API or RSS, then public structured data, then Scrapling, then Apify when it has a
  measured advantage. See `docs/source-admission.md`.
- Do not add generic `utils/`, `helpers/`, or `common/` packages. Place logic in the owning module.

## Source admission gate

A new source is not production-ready until all conditions in `docs/source-admission.md` pass.
At minimum it must have:

- explicit category and acquisition method;
- public evidence and stable identity;
- Brazil/global eligibility assessment when relevant;
- compensation semantics or an explicit unknown value;
- normalization and deduplication behavior;
- an offline fixture and parser tests;
- isolated failure and health reporting;
- no dependence on a paid service unless separately enabled and budget-limited.

## Phase 3 scope lock

Phase 3 consists of exactly two blocks, as defined by `docs/roadmap.md` and
`docs/current-work.md`:

- **3.1 — consolidate essential sources**: preserve the completed Reddit and HN admissions,
  replace or retire the indirect Algora search, verify Superteam, then freeze the source catalog.
- **3.2 — filter and prioritize**: a simple deterministic `service_domains` classifier
  (programming, automation, scraping, AI, marketing, CRM, RevOps) plus persistence/export, only
  basic quality/freshness signals, and Phase 3 closure.

Former units 3C–3H are retired as independent units. Additional sources, hackathons, Apify
acquisition, fellowships, ambassador programs, and sophisticated metrics live in the Phase 3
backlog in `docs/roadmap.md`; do not resurrect them as Phase 3 work without explicit user
approval.

Status: Phase 3 is **closed** (2026-08-14) with both blocks complete and the catalog frozen;
see the completion evidence in `docs/current-work.md`.

## Engineering rules

- Python 3.12 and PowerShell are the supported local environment.
- Activate `.venv\Scripts\activate` and run Python as `python -X utf8 ...`.
- Never hardcode API keys, cookies, passwords, tokens, or personal data. Use `.env` variables.
- Never commit `.env`, databases, reports containing personal data, browser profiles, or raw
  credentials.
- Use structured logging instead of `print()` in background code.
- Validate configuration at the boundary with typed models.
- Network tests are opt-in; the default unit suite must run offline.
- Add a sanitized fixture and parser test before changing extraction logic.
- Keep migrations backward-compatible with existing SQLite ledgers.
- Do not silently delete previously collected evidence; use lifecycle status and documented
  migrations.
- Pin or bound dependencies and document compatibility workarounds.

## Validation gates

Run after every implementation phase:

```powershell
.venv\Scripts\activate
python -X utf8 -m pytest
python -X utf8 -m ruff check .
```

Run a live collector smoke test only when network access is appropriate:

```powershell
python -X utf8 radar.py collect
python -X utf8 radar.py health
python -X utf8 radar.py report --paid-only --format detailed --limit 10
```

Before a commit or push, run:

```powershell
project-publisher check .
```

This final command requires the optional GrowthTech Publisher CLI.

Never weaken, skip, or delete a failing test merely to make a gate green.

## Documentation and Wiki contract

- `docs/mission.md`: immutable product purpose and exclusions.
- `docs/architecture.md`: boundaries and end-to-end data flow.
- `docs/module-map.md`: ownership and dependency map for every module.
- `docs/source-admission.md`: evidence standard for sources.
- `docs/sources.md`: current source inventory and confidence.
- `docs/roadmap.md`: ordered delivery plan and acceptance criteria.
- `docs/agent-runbook.md`: session and handoff procedure.
- `docs/review-findings.md`: independent audit blockers that take precedence over new features.
- `docs/current-work.md`: current autonomous work unit, ordered queue, and completion evidence.

When IDE Wiki/Knowledge becomes available, the agent must create cards for Mission, Architecture,
Module Map, Source Admission, Current Sources, and Roadmap. Each card must link to its canonical
repository document and be refreshed after the document changes. Never store secrets or personal
data in knowledge cards.

## Protected future integrations

Google Sheets, Spark/Gemini, Gmail, Hermes, OmniRoute, Oracle VPS, dashboards, notifications, and
automatic outreach are downstream integrations. Do not implement them until the relevant roadmap
prerequisites are complete. No integration may become the canonical datastore or bypass source
quality gates.
