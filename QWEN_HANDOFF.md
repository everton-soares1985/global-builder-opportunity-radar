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
Do not rewrite working architecture or start downstream Spark, Gmail, Hermes, VPS, hosted dashboard,
or outreach work before their roadmap prerequisites. A static, private local HTML briefing is the
one authorized exception; follow `docs/briefing-contract.md` exactly.

Before new roadmap work, read docs/review-findings.md and resolve every open blocking finding with
offline regression tests. Independent review blockers override previously checked roadmap items.

When the IDE Wiki/Knowledge service becomes available, build and maintain the knowledge cards
specified in docs/agent-runbook.md yourself. The cards summarize and link to canonical repository
docs; they never replace them.

Never commit, push, deploy, send messages, spend paid API credits, or expose credentials without
explicit authorization.
```

## Expected first action

Phases 1, 2, and 3 are complete. Phase 3 closed on 2026-08-14 with a frozen source catalog
(Reddit r/forhire, r/slavelabour, HN freelancer thread, Opire, Superteam Earn enabled; Algora
retired) and a deterministic seven-domain `service_domains` classifier plus basic
quality/freshness report signals. The report-hygiene correction is committed as `5f3d469`.

The user explicitly authorized **Phase 4A — local HTML briefing**. Read
`docs/briefing-contract.md`, then implement that one bounded unit. The Phase 3 backlog (additional
sources, hackathons, Apify, fellowships, sophisticated metrics), lifecycle features, AI, hosted
dashboard, and downstream integrations remain unapproved. Report after 4A; do not start anything
else.
