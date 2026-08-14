# Qwen 3.8 Max handoff

Use this file only to bootstrap a new Qwen Code session. `AGENTS.md` and `docs/` remain the
authoritative instructions.

## Initial instruction

```text
Operate as the principal implementation agent for this repository.

First read AGENTS.md and every document in its mandatory reading order. Then inspect git status,
the current branch, the relevant source modules, and their tests. Run the baseline pytest and Ruff
commands before changing files.

The product is strictly an alternative-income radar: freelance work, paid projects/contracts,
bounties, grants, prize-bearing hackathons, fellowships, and paid builder/ambassador programs.
Ordinary permanent employment belongs to Wellfound/InfoJobs and must not appear in the primary
feed.

The radar also targets paid marketing operations, CRM, lead-generation, Sales Ops, RevOps,
content, reporting, and customer-support projects where automation is a deliverable or advantage.
Keep opportunity kind separate from service domain; do not admit permanent marketing or sales
employment.

Phase 3 is locked to two blocks: 3.1 consolidates essential sources (replace or retire the
indirect Algora search, verify Superteam, then freeze the catalog) and 3.2 filters and
prioritizes (simple deterministic `service_domains` classifier covering programming, automation,
scraping, AI, marketing, CRM, and RevOps, plus only basic quality/freshness signals, then close
Phase 3). Do not resurrect retired units 3C–3H or backlog items (additional sources, hackathons,
Apify, fellowships, sophisticated metrics) without explicit approval.

Use docs/current-work.md as the operational queue and docs/roadmap.md as the phase-level plan.
Implement only the work unit marked NEXT, test it, update the canonical documentation, and report
the result using docs/agent-runbook.md. Continue one work unit at a time when all gates are green.
Do not rewrite working architecture or start downstream Spark, Gmail, Hermes, VPS, dashboard, or
outreach work before their roadmap prerequisites.

Before new roadmap work, read docs/review-findings.md and resolve every open blocking finding with
offline regression tests. Independent review blockers override previously checked roadmap items.

When the IDE Wiki/Knowledge service becomes available, build and maintain the knowledge cards
specified in docs/agent-runbook.md yourself. The cards summarize and link to canonical repository
docs; they never replace them.

Never commit, push, deploy, send messages, spend paid API credits, or expose credentials without
explicit authorization.
```

## Expected first action

Phases 1, 2, Phase 3 units 3A (Reddit admission), 3B (HN freelancer thread), and Phase 3.1
(source consolidation with a frozen catalog: Algora retired, Superteam verified) are complete.
The next work is **Phase 3.2** in `docs/current-work.md`: add the simple deterministic
`service_domains` classifier (programming, automation, scraping, AI, marketing, CRM, RevOps)
with persistence/export, add only basic quality/freshness signals, then close Phase 3. Do not
add new sources — the catalog is frozen. Stop after Phase 3 closure and report evidence.
