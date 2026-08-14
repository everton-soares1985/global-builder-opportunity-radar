# Independent review findings

Open blocking findings take precedence over new roadmap phases. An implementation agent must add
offline regression tests, fix the underlying behavior, run all validation gates, and change each
resolved checkbox to `[x]` with a short resolution note. Do not delete historical findings.

## Review 2026-08-13 — Phases 1 and 2

The existing 50 tests pass, but independent adversarial examples exposed semantic errors.

### Blocking — opportunity-kind classification

- [x] Strong traditional-employment evidence must not be overridden by an ambiguous keyword.
  Required regression: `Full-time software engineer` plus `Permanent employment contract with
  health insurance` must classify as `traditional_job`, not `contract`.
  Resolved 2026-08-13: `_TRADITIONAL_EVIDENCE` in `classification.py` matches full-time/permanent
  paired with employment substance and runs before signal counting; regression covered in
  `tests/test_review_findings.py` and `tests/test_classification.py`.
- [x] Occupational phrases must not be treated as opportunity mechanisms.
  Required regressions: a permanent `grant writer` job is not a grant; a `bounty hunter` employee
  role is not an open-source bounty.
  Resolved 2026-08-13: per-category `_OCCUPATION_BLOCKS` negative lookahead (grant → writer/manager/
  coordinator/etc.; bounty → hunter) keeps `freelance developer` and `contract developer` intact;
  regressions in `tests/test_review_findings.py`.
- [x] Alternative-income evidence must describe the engagement or reward mechanism. Preserve real
  cases such as `three-month project-based contractor engagement`, issue rewards, grant
  applications, and prize-bearing hackathons.
  Resolved 2026-08-13: added plural `issue rewards`/`paid issues` keywords; preservation cases
  parametrized in `tests/test_review_findings.py::test_real_engagement_mechanisms_preserved`.

### Blocking — structured compensation

- [x] Parsing must require currency or explicit payment context. `30 August 2026` must not parse as
  compensation.
  Resolved 2026-08-13: `parse_compensation_with_evidence` rejects candidates without currency or
  `_PAY_CONTEXT`; leading currency codes (`USD 130.00`) now parse via a new prefix group.
- [x] Infer shared magnitude correctly. `$1-2k` must produce minimum `1000` and maximum `2000`, not
  `1` and `2000`.
  Resolved 2026-08-13: when only the upper bound carries a magnitude, it is applied to the lower
  bound too; regression `test_range_shorthand_shares_upper_magnitude`.
- [x] Distinguish company metrics and aggregate pools from individual compensation. `Revenue $3M,
  bounty $100` must select the bounty value. `Prize pool $5M; individual reward $500` must not claim
  that the individual compensation is $5M. Preserve the discarded evidence when useful.
  Resolved 2026-08-13: candidate iteration with preceding-context filters (`_BUSINESS_CONTEXT`,
  `_POOL_CONTEXT` vs `_INDIVIDUAL_CONTEXT`/`_PAY_CONTEXT`) in both `extraction.py` and
  `collectors/base.py::first_compensation`; rejected snippets are returned as `discarded` evidence.
  Live smoke also exposed Opire `pendingPrice` aggregates, fixed by
  `opire.py::resolve_reward_amount` preferring an explicit title amount when the two disagree.

### Blocking — Brazil eligibility

- [x] Explicit inclusion overrides a broad regional alternative when Brazil is named: `Must be
  based in Europe or Brazil` is eligible.
  Resolved 2026-08-13: an explicit Brazil mention now ranks above non-Brazil regional restrictions.
- [x] Explicit exclusion overrides worldwide language: `Worldwide except Brazil` is ineligible.
  Resolved 2026-08-13: new `_BRAZIL_EXCLUSION` pattern is checked first.
- [x] Contradictory restrictions remain conservative and evidence-backed; add tests defining the
  chosen behavior.
  Resolved 2026-08-13: chosen contract documented in `assess_brazil_eligibility` — explicit Brazil
  exclusion always wins (e.g. `Open worldwide. Not available in Brazil.` → ineligible); otherwise
  explicit Brazil inclusion wins; regressions in `tests/test_review_findings.py`.
  Reopened 2026-08-13 (second audit): `Open to Brazil, US citizens only` classified as eligible,
  but the mandatory citizenship restriction contradicts the Brazil inclusion.
  Re-resolved 2026-08-13: refined contract — with a Brazil mention, citizenship-only restrictions
  (`US citizens only`) always contradict (ineligible), and regional restrictions contradict unless
  Brazil is named inside the same clause (`Must be based in Europe or Brazil` stays eligible).
  Regressions added for both contradiction forms in `tests/test_review_findings.py`.

### Required validation

- [x] Add focused offline regression tests for every example above.
  Resolved 2026-08-13: `tests/test_review_findings.py` plus updated `tests/test_classification.py`,
  `tests/test_extraction_structured.py`, and `tests/test_opire.py`.
- [x] Run the complete pytest and Ruff gates.
  Resolved 2026-08-13: 70 tests passed, `ruff check .` clean.
- [x] Run a live collection smoke test against enabled sources and inspect at least the top ten
  paid results for category, compensation, and eligibility plausibility.
  Resolved 2026-08-13: all four enabled sources OK; top paid rows show coherent categories
  (contract/bounty/freelance), parsed amounts (e.g. $50–80, USD 130.00), and eligibility
  (LATAM/EU listing → eligible). The one anomaly found (Opire Kickama USD 100,100 vs $50 title)
  drove the `resolve_reward_amount` fix and was re-verified at USD 50.00.
- [x] Keep Phases 1 and 2 open in `docs/roadmap.md` until all items above are resolved.
  Resolved 2026-08-13: blocker rows now checked with this resolution record.

No Phase 3 source implementation, commit, or push is authorized while this review remains open.

Status: all 2026-08-13 blocking findings resolved on 2026-08-13, including the second-audit
Brazil-eligibility contradiction (`Open to Brazil, US citizens only` → ineligible); the review is
closed.
