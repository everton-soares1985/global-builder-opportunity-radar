# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- Autonomous continuation now uses `docs/current-work.md`, with an ordered Phase 3 queue, a bounded
  Reddit source-admission unit, marketing-automation scope, and multi-window isolation rules.
- The Qwen handoff now starts from Phase 3A instead of the already completed Phase 1.
- Public setup and contributor instructions now use portable repository paths instead of
  developer-specific absolute Windows paths.

### Added

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
