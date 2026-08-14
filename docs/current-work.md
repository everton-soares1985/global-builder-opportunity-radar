# Current autonomous work

This document is the single operational handoff for the next implementation agent. Product scope
and architecture remain canonical in the other documents listed by `AGENTS.md`.

## Current position

- Current phase: **Phase 3 — source quality and expansion**.
- Completed prerequisites: Phases 1 and 2, including all independent review blockers.
- Current work unit: **3B — HN monthly freelancer thread admission**.
- Last completed unit: **3A — Reddit source expansion** (2026-08-13; evidence below).
- Downstream integrations remain blocked: dashboard, AI enrichment, Sheets, Spark/Gmail, Hermes,
  OmniRoute, and VPS scheduling.

## Work unit 3A — Reddit source expansion

```text
Roadmap phase: 3A — Reddit project-source admission
User outcome: jobbit and slavelabour can contribute paid projects without leaking ordinary jobs
Files expected to change: config/sources.yaml, the Reddit collector only if configuration is
  insufficient, sanitized fixtures, focused tests, docs/sources.md, docs/roadmap.md,
  docs/module-map.md if code ownership changes, CHANGELOG.md
Acceptance criteria: every admitted feed keeps only requester-side paid opportunities; fixtures
  cover accepted and rejected title conventions; empty/malformed feeds fail truthfully; stable IDs
  deduplicate across runs; live smoke evidence is recorded before a source becomes verified
Tests to add or update: Reddit parser/config tests using offline RSS fixtures
Live validation: one supervised smoke test per candidate feed after offline gates pass
Explicit non-goals: HN, Algora, Superteam, service-domain classification, AI, dashboards, outreach,
  applications, email sending, deployment, paid Apify usage
```

### Required implementation sequence

1. Inspect the live public feeds only to confirm their current title/flair conventions.
2. Save minimal sanitized RSS fixtures; tests must never require network access.
3. Determine whether `required_flair_prefix` is sufficient. If not, add the smallest typed
   configuration needed for an allowlist of requester-side prefixes.
4. Reject worker advertisements, ordinary employment, unpaid requests, and non-opportunity posts
   before persistence.
5. Add candidate sources disabled by default while developing.
6. Run offline tests and Ruff.
7. Run a supervised live smoke test and inspect accepted records.
8. Enable only sources that pass `docs/source-admission.md`; otherwise leave them experimental or
   disabled and record the evidence honestly.
9. Update the canonical documentation and this file with completion evidence.

## Ordered Phase 3 queue

| Unit | Scope | Prerequisite | State |
|---|---|---|---|
| 3A | Reddit `r/jobbit` and `r/slavelabour` admission | Phases 1–2 | **Complete** (2026-08-13) |
| 3B | HN monthly freelancer/seeking-freelancer thread | 3A patterns/tests | **NEXT** |
| 3C | Replace or retire indirect Algora GitHub search using official evidence | None beyond Phase 2 | Pending |
| 3D | Superteam fixture, type mapping, and reliable acquisition path | None beyond Phase 2 | Pending |
| 3E | Deterministic `service_domains` classification and persistence/export | Stable opportunity kind | Pending |
| 3F | Research and admit paid marketing/CRM/RevOps/support automation projects | 3E | Pending |
| 3G | Source confidence, freshness, and degradation metrics | Multiple admitted sources | Pending |
| 3H | Hackathon, freelance-platform, fellowship, and ambassador candidates | Admission patterns stable | Pending |

Complete one work unit per coherent diff. Do not start the next unit with failing gates or
undocumented live-source behavior.

## Marketing and business-operations scope

The radar should find paid deliverables such as CRM setup, campaign automation, lead generation,
reporting dashboards, content workflows, customer-support automation, Sales Ops, and RevOps.
It must not surface permanent marketing-manager, sales-manager, social-media-manager, or generic
operations employment. `opportunity_kind` controls whether a record belongs in the radar;
`service_domains` later describes the kind of work.

## Multi-window rule

- One writable agent per working directory and branch.
- A second coding window must use a separate Git worktree and a separate `codex/` branch.
- Split work by independent units only; do not let two agents edit shared domain, storage, config,
  roadmap, or changelog files concurrently.
- Merge or cherry-pick only after each branch passes its own tests and Ruff checks.
- If the second window is only auditing or researching, keep it read-only and have it write findings
  to the primary agent instead of editing the repository.

## Completion report required from the agent

```text
Work unit completed:
Accepted/rejected source evidence:
Offline tests:
Live smoke result:
Files changed:
Documentation updated:
Remaining risks:
Next work unit:
Commit/push status:
```

The agent may implement and validate the current unit autonomously. Commit, push, paid API usage,
deployment, outreach, applications, and messages still require explicit user authorization.

## Unit 3A completion evidence (2026-08-13)

```text
Work unit completed: 3A — Reddit project-source admission.
Accepted/rejected source evidence:
  - r/slavelabour ACCEPTED (verified): requester-side [TASK] allowlist; live smoke parsed=25
    accepted=9 (all paid task requests; [OFFER] worker ads and mod posts rejected); stable
    t3_ IDs deduplicated on re-run (inserted=1 updated=8).
  - r/jobbit REJECTED (stays disabled): live smoke parsed=25 accepted=10, dominated by yearly
    salaried job-board reposts ($115k-$300k / year) that text-evidence quarantine cannot remove
    reliably; its smoke rows moved to status 'discarded' (evidence preserved).
Offline tests: 80 tests pass (pytest -q), ruff clean; new tests/test_reddit_rss.py covers the
  allowlist, rejected conventions, empty feed, malformed XML, HTML block page, and stable IDs.
Live smoke result: both feeds fetched read-only; health output truthful; blocked/malformed
  bodies now fail truthfully instead of reporting fake empty feeds.
Files changed: src/global_builder_radar/collectors/reddit.py, src/global_builder_radar/extraction.py
  (pay-period unit recovery), config/sources.yaml, tests/test_reddit_rss.py,
  tests/test_extraction_structured.py, tests/fixtures/reddit_{jobbit,slavelabour}_sample.xml,
  tests/fixtures/reddit_malformed_body.xml, tests/fixtures/reddit_blocked_body.html.
Documentation updated: docs/sources.md, docs/roadmap.md, docs/module-map.md, CHANGELOG.md,
  this file.
Remaining risks: Reddit intermittently rate-limits (HTTP 429) or serves HTML block pages; the
  collector now reports both truthfully and source isolation keeps the batch running. slavelabour
  occasionally contains suspicious "easy money" posts; scoring/report review remains the user's
  gate before any contact.
Next work unit: 3B — HN monthly freelancer/seeking-freelancer thread.
Commit/push status: not committed (no user authorization).
```
