# Source catalog

## Enabled sources

| Source | Category | Initial method | Confidence | Notes |
|---|---|---|---|---|
| Reddit r/forhire | Freelance | Public RSS | Verified | Keep only `[Hiring]`; posts may expose email or Reddit DM. |
| Hacker News Who is Hiring | Mixed jobs/contracts | Algolia API | Degraded/disabled | Acquisition works, but ordinary jobs cannot yet be separated reliably from contracts and projects. |
| Algora-related GitHub signals | Open-source bounties | GitHub search spike | Experimental | Not an official Algora feed; keyword stuffing is rejected; replacement by the official Algora API is planned. |
| Opire | Open-source bounties | Scrapling + public Next.js data | Verified | Parses the server-provided `initialRewards` payload from `/home`. |
| Superteam Earn | Bounties/grants/hackathons | Scrapling browser | Experimental | Public `/earn/all` listing; per-item type mapping is pending; an Apify Actor is a valid fallback. |

Experimental sources are allowed to fail without stopping the collection run. Their health is
visible through `builder-radar health`.

The primary product is not a traditional job aggregator. Any source dominated by permanent jobs
stays disabled until its parser or classifier can retain only alternative-income opportunities.

## Candidate sources (researched, not implemented)

Researched 2026-08. Each candidate remains `candidate` until it passes
[`source-admission.md`](source-admission.md); implementation order follows the roadmap.

| Candidate | Category | Planned method | Research notes |
|---|---|---|---|
| Reddit r/jobbit, r/slavelabour | freelance | Public RSS (existing collector) | Config-only addition; small but fast-paid tasks. |
| HN "Ask HN: Freelancer? Seeking freelancer?" | freelance/contract | Algolia API (existing collector) | Monthly thread; config-only via `thread_query`. |
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

## Scrapling compatibility note

The project pins Scrapling 0.4.1 on Windows. Version 0.4.8 requests a Chrome 147 fingerprint that
the current BrowserForge dataset cannot generate on Windows. The pin should be revisited after the
upstream fingerprint dataset catches up.
