# Current autonomous work

This document is the single operational handoff for the next implementation agent. Product scope
and architecture remain canonical in the other documents listed by `AGENTS.md`.

## Current position

- Current phase: **Phase 3 — source quality and expansion**.
- Completed prerequisites: Phases 1 and 2, including all independent review blockers.
- Current work unit: **3A — expand Reddit project sources safely**.
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
| 3A | Reddit `r/jobbit` and `r/slavelabour` admission | Phases 1–2 | **NEXT** |
| 3B | HN monthly freelancer/seeking-freelancer thread | 3A patterns/tests | Pending |
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
