# Delivery roadmap

Phases are ordered. An autonomous agent selects the first incomplete phase whose prerequisites are
green and completes it against the listed acceptance criteria.

## Current baseline — complete

- [x] Isolated collectors and registry.
- [x] Normalized opportunity model.
- [x] SQLite persistence and deduplication.
- [x] Source health history.
- [x] Deterministic profile scoring.
- [x] Table, detailed, JSON, and CSV reports.
- [x] Five initial source experiments.
- [x] Offline unit suite and Ruff gate.

## Phase 1 — enforce the alternative-income scope

- [x] Define the mission and explicit exclusions.
- [x] Disable broad traditional-job collection until contract filtering exists.
- [x] Add a deterministic opportunity-kind classifier for `freelance`, `contract`, `bounty`,
  `grant`, `hackathon`, `paid_program`, and `traditional_job`.
- [x] Hide or quarantine `traditional_job` from the primary report.
- [x] Add fixtures for mixed-source classification.
- [x] Resolve the independent classification blockers recorded in `docs/review-findings.md`.
  Resolved 2026-08-13: employment-evidence precedence, occupation-phrase blocks, and mechanism
  preservation, with regressions in `tests/test_review_findings.py`.

Acceptance criteria: ordinary employment does not appear in the default report; project and
contract opportunities from mixed sources remain discoverable; classification is tested offline.

## Phase 2 — structured actionable fields

- [x] Add structured compensation amount/range, currency, and payment unit while preserving raw
  text.
- [x] Add deadline extraction with timezone/source evidence.
- [x] Add technology and deliverable extraction.
- [x] Add effort/duration evidence when explicitly stated.
- [x] Add Brazil eligibility with `eligible`, `ineligible`, and `unknown` states.
- [x] Resolve the compensation and Brazil-eligibility blockers in `docs/review-findings.md`.
  Resolved 2026-08-13: payment-context requirement, shared range magnitude, metric/pool
  filtering, Opire aggregate-price fix, and the conservative Brazil exclusion contract.

Acceptance criteria: no guessed values; schema migration is backward-compatible; exports contain
the new fields; extraction tests cover valid, unknown, and misleading examples.

## Phase 3 — source quality and source expansion

- [x] **3A:** Admit Reddit `r/jobbit` and `r/slavelabour` with requester-side filtering, offline RSS
  fixtures, truthful health behavior, and supervised live evidence.
  Completed 2026-08-13: r/slavelabour verified and enabled (requester-side `[TASK]` allowlist);
  r/jobbit rejected after live smoke (feed dominated by yearly salaried reposts); evidence in
  `docs/sources.md`; parser tests in `tests/test_reddit_rss.py`.
- [ ] **3B:** Admit the HN monthly freelancer/seeking-freelancer thread with offline fixtures and
  source-specific semantics instead of treating it as the broad Who Is Hiring feed.
- [ ] **3C:** Replace or retire the indirect Algora GitHub search.
- [ ] **3D:** Verify Superteam extraction with offline fixtures and explicit opportunity-type mapping.
- [ ] **3E:** Add a separate deterministic `service_domains` classifier without changing
  opportunity-kind semantics.
- [ ] **3F:** Research and admit project sources for marketing automation, CRM, lead generation,
  Sales Ops, RevOps, content automation, reporting, and customer-support automation.
- [ ] **3G:** Add source confidence, freshness, and degradation metrics.
- [ ] **3H:** Implement and admit the remaining researched candidates after the earlier admission
  patterns are stable.

Completed research prerequisites:

- [x] Research candidate sources for grants and paid fellowships (catalog in `docs/sources.md`).
- [x] Research candidate prize-bearing hackathons (catalog in `docs/sources.md`).
- [x] Research candidate freelance/project sources with public opportunity evidence (catalog in
      `docs/sources.md`).

Candidate sources must pass `docs/source-admission.md`; quantity alone is not an acceptance
criterion. The authoritative unit order and current execution contract live in
`docs/current-work.md`. A candidate described as config-only must still be verified against its
current public format before admission.

Marketing and business-operations discovery must target paid projects or contracts where
automation is useful. Do not reintroduce permanent marketing or sales employment through these
sources.

## Phase 4 — review workflow and briefing

- [ ] Add lifecycle commands: shortlist, dismiss, actioned, expired.
- [ ] Prevent previously dismissed or expired records from reappearing as new.
- [ ] Generate a concise periodic briefing with reasons, risks, and next action.
- [ ] Add configurable minimum quality and freshness thresholds.

Acceptance criteria: the user can process a shortlist without editing SQLite manually and repeated
runs preserve decisions.

## Phase 5 — optional AI enrichment

- [ ] Define a provider-neutral classification interface.
- [ ] Require structured JSON output with schema validation.
- [ ] Cache by opportunity content hash.
- [ ] Keep deterministic fallback and record model/provider/version.
- [ ] Add budget and concurrency limits.

AI may estimate fit and effort but must label estimates and may not invent eligibility,
compensation, deadlines, or contacts.

## Phase 6 — dashboard

- [ ] Build a read-first dashboard inspired by information-dense monitoring tools.
- [ ] Provide source health, filters, shortlist, evidence, and lifecycle controls.
- [ ] Keep SQLite/service APIs as the source of truth; never parse terminal output.

Acceptance criteria: the dashboard works locally, does not duplicate pipeline logic, and exposes
provenance for every result.

## Phase 7 — downstream automation

- [ ] Google Sheets projection.
- [ ] Spark/Gemini briefing or message drafting.
- [ ] Explicitly authorized Gmail delivery workflow.
- [ ] Hermes/OmniRoute orchestration.
- [ ] Oracle VPS scheduling, health checks, and recovery.

These integrations remain blocked until Phases 1–4 are complete and stable. Automatic outreach
requires a separate explicit authorization and safety design.
