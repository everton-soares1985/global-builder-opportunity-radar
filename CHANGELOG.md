# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- Report hygiene fix (2026-08-14): the default report now excludes rows from retired/disabled
  sources (audit override: `--include-disabled-sources`), and a new read-only
  `verify-github-issues` command hides closed or dead-reference GitHub issues (status
  `discarded`, preserved in SQLite) and strips pay from open zero-bounty issues. Zero amounts
  can never be extracted as compensation. First run hid 22 contaminated rows; reports regenerated.
- Autonomous continuation now uses `docs/current-work.md`, with an ordered Phase 3 queue, a bounded
  Reddit source-admission unit, marketing-automation scope, and multi-window isolation rules.
- The Qwen handoff now starts from Phase 3A instead of the already completed Phase 1.
- Public setup and contributor instructions now use portable repository paths instead of
  developer-specific absolute Windows paths.
- Phase 3A admission decision (2026-08-13): Reddit r/slavelabour is verified and enabled with a
  requester-side `[TASK]` title allowlist; Reddit r/jobbit stays disabled after the supervised
  live smoke showed its `[HIRING]` feed is dominated by yearly salaried job-board reposts. Its
  smoke rows remain in the ledger with status `discarded` for audit.
- Phase 3B admission decision (2026-08-14): the HN monthly Freelancer/Seeking-freelancer thread
  is verified and enabled through the dedicated `hackernews_freelancer` collector; the broad
  Who-is-Hiring collector stays disabled. Worker ads (`SEEKING WORK`), chatter, and flagged
  comments are rejected before persistence; a month without requester posts reports a truthful
  zero instead of a failure.
- Phase 3 simplified into two blocks (3.1 consolidate essential sources, 3.2 filter and
  prioritize); former units 3C–3H retired, their scope moved to the Phase 3 backlog in
  `docs/roadmap.md`.
- Phase 3.1 decision (2026-08-14): the indirect Algora GitHub search is retired (disabled) —
  no official Algora integration is built in Phase 3; Superteam Earn is verified with offline
  fixtures and live smoke; the source catalog is frozen at Reddit r/forhire, r/slavelabour, HN
  freelancer thread, Opire, and Superteam Earn until Phase 3.2 closes Phase 3.
- Phase 3.2 (2026-08-14) closes Phase 3: a deterministic `service_domains` classifier labels
  opportunities with the seven service areas (programming, automation, scraping, AI, marketing,
  CRM, RevOps); unknown stays unknown. Labels are persisted and exported but never influence
  opportunity kind, quarantine, or ranking. Basic quality and freshness are report-only signals.

### Added

- Phase 4A (2026-08-15): `radar.py briefing` renders every eligible, non-discarded opportunity
  from enabled sources into one private, self-contained HTML report (default
  `reports/briefing.html`). Cards show stored evidence (pay, deadline, Brazil eligibility,
  location/remote, technologies, effort, contact path), honest `Unknown` states, deterministic
  "Why it surfaced" and "Next action" notes, and an "Open original opportunity" link. Optional
  filters: `--paid-only`, `--min-score`, `--max-age`, `--limit` (0 = unlimited); `--open` opens
  the finished file in the default browser. The command is read-only: no collection, no GitHub
  verification, no SQLite mutation, no AI, no external side effects. Renderer is the pure,
  offline-testable module `briefing.py`; tests in `tests/test_briefing.py`.
- Reddit collector option `allowed_title_prefixes` (case-insensitive requester-side allowlist)
  alongside the legacy single-prefix `required_flair_prefix`.
- Sanitized offline RSS fixtures for r/jobbit and r/slavelabour covering accepted and rejected
  title conventions, plus malformed-XML and HTML-block-page bodies; offline parser tests in
  `tests/test_reddit_rss.py`.
- `hackernews_freelancer` collector for the monthly "Freelancer? Seeking freelancer?" thread
  with a requester-side comment allowlist (`allowed_comment_prefixes`), sanitized thread fixture
  `tests/fixtures/hn_freelancer_thread_sample.json`, and offline parser tests in
  `tests/test_hn_freelancer.py`.
- `parse_listing_page` in the Scrapling collector: the listing-card normalization is now a pure,
  offline-testable function with sanitized Superteam fixture
  `tests/fixtures/superteam_listing_sample.html` and parser tests in
  `tests/test_scrapling_links.py`.
- `service_domains.py`: deterministic seven-domain service-area classifier with offline tests in
  `tests/test_service_domains.py`; the pipeline labels every opportunity after enrichment.
- Additive SQLite column `service_domains_json` (legacy ledgers default to `'[]'`); JSON/CSV
  exports and reports now include `service_domains`, `freshness_days`, and `quality_score`.
- `basic_quality` and `freshness_days` report signals in `scoring.py` (report-only; ranking is
  unchanged).

- Structured evidence extraction (`extraction.py`): compensation amount/range/currency/unit,
  explicit deadlines with source evidence, technology list, effort evidence, and Brazil
  eligibility (`eligible`/`ineligible`/`unknown`). Unknown values are never guessed.
- Pipeline enrichment applies structured extraction after classification.
- Additive SQLite migration adds the new structured columns to existing ledgers without data
  loss; exports (JSON/CSV) now include them.
- Deterministic opportunity-kind classifier (`classification.py`) covering freelance, contract,
  bounty, grant, hackathon, paid_program, and traditional_job, with mixed-source fixtures under
  `tests/fixtures/opportunity_kind_samples.json`.
- Pipeline now classifies every collected opportunity before scoring.
- Storage quarantine now hides both legacy `direct_job` and classified `traditional_job` records
  from default reports.
- Offline tests for classification, pipeline failure isolation, and the expanded quarantine.
- Category weights for `contract`, `paid_program`, and `traditional_job` in the profile rules.
- Candidate source catalog in `docs/sources.md` covering researched freelance, bounty, grant,
  hackathon, contract, and paid-program sources with planned acquisition methods.
- Roadmap Phase 3 now records completed source research and the recommended implementation order.
- Wiki knowledge cards derived from the canonical docs (Mission, Architecture, Module Map, Source
  Admission, Current Sources, Roadmap).
- Initial source-driven architecture.
- RSS, API, GitHub search, Scrapling, and optional Apify collector adapters.
- SQLite persistence, deterministic scoring, deduplication, and CLI reporting.
- Initial source catalog for Reddit, Hacker News, Algora, Opire, and Superteam Earn.
- Windows-compatible Scrapling 0.4.1 pin with the upstream 0.4.8 fingerprint limitation documented.
- Paid, contact, category, and source report filters.
- Detailed reports with descriptions, contacts, compensation evidence, and source links.
- Canonical mission, module map, source-admission standard, autonomous-agent runbook, delivery
  roadmap, and Qwen handoff.

### Fixed

- `first_compensation` no longer reports aggregate prize pools named after the amount (e.g.
  "$10,000 prize pool") as individual pay; surfaced by the Superteam fixture.

### Changed

- Compensation extraction now rejects funding, revenue, market-size, and transaction-volume
  figures using nearby context.
- Profile scoring now uses word boundaries plus category and source weights.
- The experimental GitHub bounty collector rejects obvious keyword stuffing.
- Product scope is now strictly alternative income outside traditional employment.
- Broad Hacker News job collection is disabled until contract-only classification is reliable.
- Legacy `direct_job` records are hidden from reports by default and remain available only through
  the explicit `--include-traditional` audit flag.
- Independent semantic review findings now block subsequent roadmap phases until regression-tested
  classification, compensation, and eligibility fixes are complete.
- The mission now includes paid marketing, CRM, lead-generation, Sales Ops, RevOps, content,
  reporting, and support projects where automation is a core service, while keeping permanent
  employment excluded.

### Fixed

- Independent review 2026-08-13 (see `docs/review-findings.md`): explicit full-time/permanent
  employment evidence now outranks ambiguous alternative keywords; occupation phrases such as
  "grant writer" and "bounty hunter" are no longer classified as opportunity mechanisms.
- Compensation parsing now requires currency or explicit payment context (`30 August 2026` is no
  longer parsed as pay), shares range magnitude for shorthand like `$1-2k`, supports leading
  currency codes (`USD 130.00`), and skips corporate metrics and aggregate prize pools while
  preserving the discarded evidence.
- Brazil eligibility now resolves explicit exclusions (`Worldwide except Brazil` → ineligible)
  and explicit inclusions inside regional clauses (`Europe or Brazil` → eligible), with a
  documented conservative contract for contradictory text.
- Brazil eligibility treats mandatory restrictions as contradicting a Brazil inclusion:
  citizenship-only requirements (`Open to Brazil, US citizens only` → ineligible) always
  contradict, and regional requirements contradict unless Brazil is named in the same clause.
- Opire rewards prefer an explicit amount stated in the issue title when the API `pendingPrice`
  disagrees (fixes aggregate figures such as USD 100,100 being claimed for a $50 bounty).
- Collector compensation selection (`first_compensation`) uses preceding context only, so company
  metrics and prize pools no longer shadow nearby individual amounts.
- The Reddit feed parser now reports blocked or malformed feed bodies as truthful failures
  (`feed_parse_failed`) instead of silent empty results: bozo feeds with no entries and non-feed
  bodies (e.g. HTML block pages parsed with `bozo=0`) are both distinguished from legitimately
  empty feeds.
- Compensation enrichment recovers the pay-period unit from the full title/description evidence
  when the collector snippet loses the suffix (`$5/hr` no longer records unit `fixed`).
