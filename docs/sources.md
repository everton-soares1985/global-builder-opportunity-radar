# Source catalog

## Enabled sources

| Source | Category | Initial method | Confidence | Notes |
|---|---|---|---|---|
| Reddit r/forhire | Freelance | Public RSS | Verified | Keep only `[Hiring]`; posts may expose email or Reddit DM. |
| Reddit r/slavelabour | Freelance | Public RSS | Verified | Admitted 2026-08-13 (unit 3A). Keep only requester-side `[TASK]` posts via `allowed_title_prefixes`; `[OFFER]` worker ads and mod posts are rejected before persistence. Live smoke: 25 parsed / 9 accepted, all paid task requests; stable `t3_` IDs deduplicate across runs. |
| HN monthly Freelancer/Seeking-freelancer thread | Freelance/contract | Algolia API | Verified | Admitted 2026-08-14 (unit 3B). Newest monthly thread only; top-level `SEEKING FREELANCER` comments become opportunities, `SEEKING WORK` worker ads, chatter, and flagged comments are rejected. Live smoke: August thread truthful zero (15 parsed / 0 accepted); June thread cross-check accepted the single real requester post of 31 comments. |
| Hacker News Who is Hiring | Mixed jobs/contracts | Algolia API | Degraded/disabled | Acquisition works, but ordinary jobs cannot yet be separated reliably from contracts and projects. |
| Algora-related GitHub signals | Open-source bounties | GitHub search spike | Retired | Retired 2026-08-14 (Phase 3.1): indirect GitHub keyword search fails `source-admission.md`; disabled rather than replaced now. Ledger rows remain as evidence; official integration is backlog. |
| Opire | Open-source bounties | Scrapling + public Next.js data | Verified | Parses the server-provided `initialRewards` payload from `/home`. |
| Superteam Earn | Bounties/grants/hackathons | Scrapling browser | Verified | Verified 2026-08-14 (Phase 3.1). `/earn/listing/` cards parsed offline-testably via `parse_listing_page` (fixture `tests/fixtures/superteam_listing_sample.html`); bounties tab currently yields Bounty-type cards with individual USDC/USDG amounts, no ordinary employment. Freeze run: 22 links matched, stable IDs (0 inserted / 22 updated). |

Experimental sources are allowed to fail without stopping the collection run. Their health is
visible through `builder-radar health`.

The primary product is not a traditional job aggregator. Any source dominated by permanent jobs
stays disabled until its parser or classifier can retain only alternative-income opportunities.

### Catalog freeze (Phase 3.1, 2026-08-14)

The source catalog is frozen at Phase 3.1 closure: the enabled set is Reddit r/forhire, Reddit
r/slavelabour, HN freelancer thread, Opire, and Superteam Earn; `algora_bounties`,
`hackernews_hiring`, and `reddit_jobbit` stay disabled with the reasons above. No new sources are
admitted until Phase 3.2 closes Phase 3; candidates stay in the backlog below.

Freeze-run health (2026-08-14): reddit_forhire OK (25 parsed / 5 accepted), hackernews_freelancer
OK (truthful zero, 15 parsed / 0 accepted), opire_bounties OK (30 accepted), superteam_earn OK
(22 matched); reddit_slavelabour FAILED with isolated truthful 429 rate-limit (verified source,
smoke evidence 2026-08-13). A failing source did not stop the remaining sources.

## Candidate sources (researched, not implemented)

Researched 2026-08. Each candidate remains `candidate` until it passes
[`source-admission.md`](source-admission.md); implementation order follows the roadmap.

| Candidate | Category | Planned method | Research notes |
|---|---|---|---|
| Algora official | bounty, contract | GraphQL API (`api.algora.io`) | Replaces the GitHub search spike; official bounties and contract work with values and repos. |
| Dework | bounty (web3) | Scrapling or internal JSON at `app.dework.xyz/bounties` | Investigate a Next.js-style payload as with Opire. |
| DoraHacks | bounty, grant, hackathon | Scrapling | Covers three categories in one platform. |
| Contra | freelance, contract | Scrapling | Public gigs; many automation/AI projects; no commission model. |
| Upwork | freelance | Apify actor `lentic_clockss/upwork-jobs-scraper` | No-login public jobs feed. |
| Freelancer.com | freelance, contract | Apify actor `automation-lab/freelancer-jobs-scraper` | Structured budgets and skills. |
| MLH | hackathon | Scrapling | Simple public events calendar. |
| Devpost | hackathon | Apify actor `automation-lab/devpost-scraper` | Prizes, deadlines, themes. |
| Unstop | hackathon | Apify actor `trusted_offshoot/unstop-hackathon-scraper` | Many cash-prize events. |
| Superteam agents endpoint | bounty, grant | Agent-facing listing API documented at `superteam.fun/earn/agents/` | May replace browser scraping; needs manual verification. |
| Paid fellowships (MLH Fellowship, GSoC, Outreachy, LFX Mentorship, Season of Docs) | paid_program | Curated seasonal source | Fixed application windows; community-maintained program lists exist on GitHub. |
| Web3 ambassador programs | paid_program | Scrapling `web3.career/ambassador-jobs` | Rolling applications; several pay monthly stipends. |

Rejected after research: IssueHunt (pivoted to security bug bounties), Zealy/Galxe (token-only
rewards, admin-gated APIs), Fiverr (buyer-oriented, no opportunity feed), `aurumworks`
hackathon-aggregator actor (deprecated), and Remotive/RemoteOK/WWR/python.org jobs (dominated by
permanent employment, out of scope per `mission.md`).

Rejected after implementation: Reddit r/jobbit (unit 3A, 2026-08-13). The `[HIRING]` feed is
dominated by yearly salaried job-board reposts (e.g. `/u/Varqu` devitjobs links, `$115k–$300k /
year`); live smoke showed 10/25 accepted and most were ordinary employment that text-evidence
quarantine cannot remove reliably. The config entry stays disabled and its smoke rows are kept in
the ledger with status `discarded` for audit. Algora-related GitHub signals (Phase 3.1,
2026-08-14) were retired: the indirect keyword search is a fragile proxy with no official endpoint
used; the source is disabled and an official Algora path stays in the Phase 3 backlog and is not
planned for Phase 3. r/slavelabour from the same research batch was
admitted instead (see enabled sources).

## Scrapling compatibility note

The project pins Scrapling 0.4.1 on Windows. Version 0.4.8 requests a Chrome 147 fingerprint that
the current BrowserForge dataset cannot generate on Windows. The pin should be revisited after the
upstream fingerprint dataset catches up.
