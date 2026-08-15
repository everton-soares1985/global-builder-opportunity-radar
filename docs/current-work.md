# Current autonomous work

This document is the single operational handoff for the next implementation agent. Product scope
and architecture remain canonical in the other documents listed by `AGENTS.md`.

## Current position

- Current phase: **Phase 4A — local HTML briefing** implemented and validated (2026-08-15);
  awaiting Everton's real-world review and an explicit commit authorization. Phase 3 remains
  closed; its former units 3C–3H are retired and live in the roadmap backlog.
- Completed prerequisites: Phases 1, 2, and 3, including all independent review blockers.
- Current work unit: **4A — local HTML briefing** — delivered per
  [`briefing-contract.md`](briefing-contract.md); completion evidence below. Stop here: do not
  start lifecycle actions (4B) or any AI integration without a separate explicit decision.
  The post-Phase-3 report-hygiene correction is committed as `5f3d469`; do not reopen it.
- Last completed units: **3A — Reddit source expansion** (2026-08-13), **3B — HN freelancer
  thread admission** (2026-08-14), **Phase 3.1 — consolidate essential sources** (2026-08-14,
  catalog frozen), and **Phase 3.2 — filter and prioritize** (2026-08-14); evidence below.
- Downstream integrations remain blocked: hosted dashboard, AI enrichment, Sheets, Spark/Gmail,
  Hermes, OmniRoute, and VPS scheduling. A static local HTML report is authorized and is not a
  hosted dashboard.

## Work unit 4A — local HTML briefing (COMPLETE 2026-08-15)

```text
Roadmap phase: 4A — local HTML briefing
User outcome: one private, polished HTML file opens locally and shows every eligible opportunity
with its evidence, unknowns, next action, and source link; no terminal review required.
Canonical contract: docs/briefing-contract.md
Files expected to change: cli.py, a focused briefing renderer module, tests/, README.md,
docs/module-map.md, CHANGELOG.md, .gitignore, this file.
Acceptance criteria: every card is evidence-backed and escaped; no SQLite mutation; no server,
AI, profile inference, deployment, or external side effect; generated report is Git-ignored.
Tests to add: pure HTML renderer, factual grouping, unknown evidence, hostile text escaping,
enabled-source filtering, and no store mutation.
Live validation: generate a briefing from the real local ledger after offline gates.
Explicit non-goals: lifecycle, AI, tailored applications, email/outreach, Sheets, domain hosting,
dashboard server, Hermes, OmniRoute, VPS.
Commit/push: requires a separate explicit user authorization after Qwen reports the diff and gates.
```

## Work unit Phase 3.1 — consolidate essential sources

```text
Roadmap phase: 3.1 — consolidate essential sources
User outcome: a small frozen set of verified sources feeds the radar without ordinary jobs
Files expected to change: collectors/github_bounties.py or its retirement, collectors/opire.py or
  collectors/scrapling_links.py only as needed for Superteam, config/sources.yaml, sanitized
  fixtures, focused tests, docs/sources.md, docs/roadmap.md, docs/module-map.md, CHANGELOG.md
Acceptance criteria: Algora is replaced by official evidence or retired with honest records;
  Superteam has offline fixtures and explicit opportunity-type mapping; every enabled source
  passes docs/source-admission.md; the catalog freeze is recorded in this file and sources.md
Tests to add or update: offline parser tests for any changed extraction
Live validation: one supervised smoke test per changed source after offline gates pass
Explicit non-goals: new sources, hackathons, Apify, fellowships, service-domain classification,
  metrics, AI, dashboards, outreach, deployment
```

### Required implementation sequence

1. Gather official evidence about Algora (official API or its absence) and decide replace or
   retire; record the decision honestly.
2. If replacing, add the smallest typed configuration and sanitized fixtures; if retiring, keep
   ledger evidence with lifecycle status and update the docs.
3. Verify Superteam with sanitized fixtures and an explicit opportunity-type mapping.
4. Run offline tests and Ruff, then supervised live smoke tests for changed sources.
5. Freeze the catalog: mark every source verified/experimental/degraded/retired in
   `docs/sources.md` and record the freeze here.

## Work unit Phase 3.2 — filter and prioritize (preview)

```text
Roadmap phase: 3.2 — filter and prioritize
Scope: simple deterministic service_domains classifier (programming, automation, scraping, AI,
  marketing, CRM, RevOps) plus persistence/export; only basic quality/freshness signals; then
  close Phase 3 with recorded evidence
Constraints: opportunity_kind semantics stay unchanged; unknown domains stay unknown; no
  permanent employment reintroduced; deterministic offline validation remains available
```

## Ordered Phase 3 queue

| Unit | Scope | Prerequisite | State |
|---|---|---|---|
| 3A | Reddit `r/jobbit` and `r/slavelabour` admission | Phases 1–2 | **Complete** (2026-08-13) |
| 3B | HN monthly freelancer/seeking-freelancer thread | 3A patterns/tests | **Complete** (2026-08-14) |
| 3.1 | Consolidate essential sources: replace/retire indirect Algora, verify Superteam, freeze catalog | 3A/3B | **Complete** (2026-08-14) |
| 3.2 | Filter and prioritize: `service_domains` classifier + basic quality/freshness, close Phase 3 | 3.1 | **Complete** (2026-08-14) |

Former units 3C–3H are retired as independent units; their scope either folds into 3.1/3.2 or
moves to the Phase 3 backlog in `docs/roadmap.md` (additional sources, hackathons, Apify,
fellowships, sophisticated metrics).

Complete one work unit per coherent diff. Do not start the next unit with failing gates or
undocumented live-source behavior.

## Marketing and business-operations scope

The radar should find paid deliverables such as CRM setup, campaign automation, lead generation,
reporting dashboards, content workflows, customer-support automation, Sales Ops, and RevOps.
It must not surface permanent marketing-manager, sales-manager, social-media-manager, or generic
operations employment. `opportunity_kind` controls whether a record belongs in the radar;
`service_domains` (Phase 3.2) describes the kind of work and must cover at least programming,
automation, scraping, AI, marketing, CRM, and RevOps. Researching additional marketing/CRM/RevOps
sources is deferred to the Phase 3 backlog.

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

## Unit 3B completion evidence (2026-08-14)

```text
Work unit completed: 3B — HN monthly freelancer/seeking-freelancer thread admission.
Accepted/rejected source evidence:
  - Thread convention confirmed live: worker ads use the SEEKING WORK prefix; requester posts
    use SEEKING FREELANCER. The collector keeps only top-level SEEKING FREELANCER comments.
  - Live smoke (August 2026 thread, id 49157021): parsed=15 accepted=0 — truthful zero, the
    month currently contains only worker ads; health distinguishes this from a failure.
  - Cross-check (June 2026 thread, id 48358236): parsed=31 accepted=1; the single real
    SEEKING FREELANCER post was accepted with correct title/URL/provenance, all 28 SEEKING WORK
    ads, chatter, and flagged comments rejected.
Offline tests: 87 tests pass (pytest -q), ruff clean; new tests/test_hn_freelancer.py covers
  requester acceptance, worker-ad/chatter/flagged/empty rejection, nested-reply exclusion,
  truthful zeros, and stable IDs over a sanitized thread fixture.
Live smoke result: read-only Algolia API calls only; failures are isolated at the collector
  boundary and reported truthfully.
Files changed: src/global_builder_radar/collectors/hackernews.py, registry.py,
  config/sources.yaml, tests/test_hn_freelancer.py,
  tests/fixtures/hn_freelancer_thread_sample.json.
Documentation updated: docs/sources.md, docs/roadmap.md, docs/module-map.md, CHANGELOG.md,
  this file.
Remaining risks: requester posts are sparse (roughly 0-2 per monthly thread), so most runs
  report truthful zeros; the broad Who-is-Hiring collector remains disabled and degraded.
Next work unit: 3C — replace or retire the indirect Algora GitHub search.
Commit/push status: see git history (separate commit from unit 3A).
```

## Phase 3.1 completion evidence (2026-08-14)

```text
Work unit completed: Phase 3.1 — consolidate essential sources.
Accepted/rejected source evidence:
  - Algora RETIRED (disabled): the indirect GitHub keyword search fails source-admission.md;
    no official Algora integration built in Phase 3 (backlog). Config entry kept with a
    retirement comment; ledger rows remain as evidence.
  - Superteam ACCEPTED (verified): parse_listing_page extracted as a pure offline-testable
    parser; sanitized fixture covers card parsing, dedup, non-listing rejection, truthful empty
    page, and max_items. Live smoke: 22 listing cards, all Bounty-type with individual
    USDC/USDG amounts, no ordinary employment; stable IDs (inserted=0 updated=22).
  - Catalog FROZEN: enabled set is reddit_forhire, reddit_slavelabour, hackernews_freelancer,
    opire_bounties, superteam_earn; algora_bounties, hackernews_hiring, reddit_jobbit disabled
    with documented reasons. No new sources until Phase 3.2 closes Phase 3.
Offline tests: 94 tests pass (pytest -q), ruff clean; new tests/test_scrapling_links.py (7
  tests) over tests/fixtures/superteam_listing_sample.html.
Live smoke result: freeze run 2026-08-14 — reddit_forhire OK (25 parsed / 5 accepted),
  hackernews_freelancer OK (truthful zero), opire_bounties OK (30 accepted), superteam_earn OK
  (22 matched); reddit_slavelabour FAILED with isolated truthful 429 rate-limit (source already
  verified 2026-08-13). The failing source did not stop the batch.
Files changed: src/global_builder_radar/collectors/scrapling_links.py (parse_listing_page),
  src/global_builder_radar/collectors/base.py (prize-pool-after-amount fix), config/sources.yaml,
  tests/test_scrapling_links.py, tests/fixtures/superteam_listing_sample.html.
Documentation updated: docs/sources.md (retirement, verification, freeze), docs/roadmap.md,
  CHANGELOG.md, this file.
Remaining risks: Superteam uses browser scraping (card selectors may change; the truthful-empty
  failure mode covers that); the current tab yields only Bounty-type cards, grants/hackathons
  tabs are backlog; Reddit rate limits remain intermittent but isolated.
Next work unit: Phase 3.2 — service_domains classifier (programming, automation, scraping, AI,
  marketing, CRM, RevOps) + basic quality/freshness, then close Phase 3.
Commit/push status: pending user authorization.
```

## Phase 3.2 completion evidence (2026-08-14) — Phase 3 CLOSED

```text
Work unit completed: Phase 3.2 — filter and prioritize; Phase 3 closed.
Scope delivered:
  - service_domains.py: deterministic keyword classifier with exactly seven domains
    (ai, automation, crm, marketing, programming, revops, scraping); unknown stays unknown
    (empty list); labels never touch opportunity kind, quarantine, or ranking.
  - Persistence: additive service_domains_json column (schema + legacy migration default '[]'),
    pipeline labels every opportunity after enrichment, upsert persists it.
  - Exports/reports: JSON and CSV now include service_domains, freshness_days, and
    quality_score; table and detailed reports show Domains/Age/Quality columns.
  - Basic signals only: basic_quality = four evidence checks (pay, description >= 80 words,
    contact, date evidence) at 0.25 each; freshness_days = age from published_at/first_seen_at.
    No AI, no new sources, no sophisticated metrics.
Offline tests: 105 tests pass (pytest -q), ruff clean; new tests/test_service_domains.py
  (7 domains, boundaries, unknown, tags/description sources, kind independence), plus scoring
  and storage tests for the new signals, migration default, and pipeline persistence.
Ledger evidence: frozen-catalog re-collection labeled refreshed rows; a one-off offline backfill
  re-derived domains from stored text for older rows (114/210 labeled); remaining rows are
  honestly unknown. Reports regenerated (reports/opportunities.{json,csv}).
Files changed: src/global_builder_radar/service_domains.py (new), models.py, storage.py,
  pipeline.py, scoring.py, cli.py, tests/test_service_domains.py (new), tests/test_scoring.py,
  tests/test_storage.py, tests/test_pipeline.py.
Documentation updated: docs/roadmap.md (Phase 3 closure), docs/module-map.md, CHANGELOG.md,
  QWEN_HANDOFF.md, this file.
Remaining risks: keyword labels carry normal deterministic noise (e.g. video-editing posts can
  pick up automation); the catalog stays frozen, so label coverage grows only with refreshed
  rows; Phase 4 (review workflow/briefing) is not started.
Next work unit: none — Phase 3 is closed; await user direction for Phase 4.
Commit/push status: pending user authorization.
```

## Report hygiene fix evidence (2026-08-14) — post-Phase-3 operational correction

```text
Trigger: user review of the real report found contaminated rows — a retired-source bounty,
  closed GitHub issues shown as open opportunities, and a zero-bounty issue shown as $1,500 pay.
Scope delivered (report-only, no new sources/architecture):
  - Default report excludes rows from disabled/retired sources via enabled_sources filter
    (rows stay in SQLite; audit override: report --include-disabled-sources).
  - New read-only CLI command verify-github-issues checks every non-discarded GitHub issue
    row against the public API (redirect-following): closed issues and dead references
    (HTTP 404/410) become status='discarded'; open issues labeled zero-bounty lose all
    compensation fields. Everything is preserved in SQLite.
  - Zero amounts can never be extracted as pay: first_compensation skips values <= 0
    (including token suffixes) and Opire resolve_reward_amount rejects zero title/pending
    amounts.
  - New module github_issues.py: pure URL mapping (issue links only) and state/label verdict;
    offline-testable without network.
Offline tests: 116 tests pass (pytest -q), ruff clean; new tests/test_github_issues.py plus
  additions to test_extraction.py, test_opire.py, and test_storage.py (filter, discard,
  clear_compensation, github_issue_rows).
Live evidence: two supervised verify-github-issues runs hid 22 rows — 18 closed issues
  (including qtop #433/#337, autokey #87, MisakaNet #932) and 4 dead references (404/410);
  remaining 11 issue rows verified open. No open zero-bounty rows were found this run.
Files changed: src/global_builder_radar/github_issues.py (new), cli.py, storage.py,
  collectors/base.py, collectors/opire.py, tests/test_github_issues.py (new),
  tests/test_extraction.py, tests/test_opire.py, tests/test_storage.py, CHANGELOG.md, this file.
Remaining risks: issues can close between verifications — rerun verify-github-issues before
  acting on old rows; closed-state evidence exists only at GitHub, not in stored payloads.
Next work unit: none — await user assessment of the cleaned report before any Phase 4 decision.
Commit/push status: pending user authorization.
```

## Unit 4A completion evidence (2026-08-15)

```text
Work unit completed: 4A — local HTML briefing.
Scope delivered:
  - briefing.py: pure deterministic renderer. Every source-derived value is HTML-escaped;
    non-HTTP(S) URLs never become links; unknown values render as `Unknown`; no raw payload,
    credential, or hidden metadata reaches the HTML. Cards carry title, source, kind, domains,
    score, age, quality, pay, deadline, Brazil eligibility, location/remote, technologies,
    effort, contact path, description excerpt with full text in a native <details>, a factual
    "Why it surfaced" list, a factual "Next action" list, and an "Open original opportunity"
    link (new tab, rel=noopener).
  - Factual grouping: Ready to review (stored pay evidence), Needs details (missing evidence),
    Brazil unavailable (explicitly ineligible); header shows generation time, applied filters,
    card count, and an evidence disclaimer. Inline vanilla-JS text/source filtering only; no
    framework, CDN, font, image, analytics, or server.
  - cli.py `briefing` command: reads the SQLite ledger read-only (enabled sources only,
    non-discarded, alternative-income), writes self-contained HTML (default
    reports/briefing.html), prints path and truthful card/omitted counts. Filters: --paid-only,
    --min-score, --max-age, --limit (0 = unlimited); --open opens the finished file locally.
    No collection, no GitHub verification, no SQLite mutation, no AI, no other side effects.
Offline tests: 129 tests pass (pytest -q), ruff clean; new tests/test_briefing.py covers
  hostile-text escaping, unsafe-URL neutralization, required card evidence, honest unknown
  states, factual grouping and filters, disabled-source exclusion via the CLI, truthful empty
  counts, and no-ledger-mutation.
Live validation: `radar.py briefing` against the real local ledger produced 81 cards
  (Ready to review + Needs details; no Brazil-unavailable rows) at reports/briefing.html;
  `--open` opened the file in the default browser; HTML inspected for groups, disclaimer,
  and absence of external resources or raw payloads.
Files changed: src/global_builder_radar/briefing.py (new), cli.py, tests/test_briefing.py
  (new), README.md, docs/module-map.md, docs/roadmap.md, CHANGELOG.md, this file.
  (`reports/*.html` was already Git-ignored.)
Remaining risks: descriptions from forum sources can be noisy; grouping uses only stored pay
  and eligibility evidence, so "Ready to review" still requires manual confirmation against
  the original listing; the ledger snapshot predates a fresh collect run.
Next work unit: none — await Everton's review of the HTML briefing; 4B lifecycle commands and
  any AI briefs require separate explicit authorization (see briefing-contract.md follow-on).
Commit/push status: pending user authorization.
```
