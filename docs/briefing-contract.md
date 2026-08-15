# Briefing HTML local — contract

## Purpose

Turn the existing SQLite ledger into one private, readable browser page so Everton can review
**every eligible opportunity found by the radar**, understand the factual evidence, open the
original listing, and apply manually. This is a report artifact, not a hosted dashboard.

## Scope: Phase 4A only

Implement one CLI command:

```powershell
python -X utf8 radar.py briefing
```

It must read only from the canonical SQLite ledger and generate a self-contained local HTML file
under `reports/`. It must not start a web server, deploy to `growthtech.solutions`, call an LLM,
send e-mail, write to a Google service, or change opportunity lifecycle state.

## Command contract

Suggested interface (small deviations are allowed only when they improve consistency with the
existing `report` command):

```text
briefing [--output PATH] [--limit N] [--min-score N] [--paid-only]
         [--max-age DAYS] [--open]
```

- Default output: `reports/briefing.html`.
- By default include every non-discarded, enabled-source, alternative-income record. Do not hide
  records merely because compensation, deadline, Brazil eligibility, or contact is unknown.
- `--paid-only`, `--min-score`, and `--max-age` are optional narrowing filters; `--limit 0` means
  no limit. Use a finite default only if rendering the full local ledger proves impractical, and
  print the count shown versus omitted truthfully.
- `--open` may open the generated file in the user's default browser only after writing it.
- The command prints the saved file path and number of cards. It does not collect, verify GitHub,
  or mutate records.

## Card contract

Every included opportunity gets a card with:

1. title, source, opportunity kind, service domains, score, age, and quality;
2. explicit pay, deadline, Brazil eligibility, location/remote, technologies, effort, and contact
   path where stored; unknown values must render as `Unknown`, never guessed;
3. a short normalized description excerpt with the full original description available by
   expanding a native HTML `<details>` element;
4. a deterministic **Why it surfaced** section based only on stored facts (for example: pay
   evidence, matching service domains, recency, and score) — no claims of personal experience or
   fit beyond those facts;
5. a deterministic **Next action** section: open original source; use the stated contact/form if
   present; verify missing or stale details before applying;
6. a visible `Open original opportunity` link that opens the stored public URL in a new tab.

Cards may be grouped by transparent review priority, but grouping must remain factual and all
included cards must be visible. Recommended groups:

- `Ready to review`: paid evidence and not explicitly Brazil-ineligible;
- `Needs details`: unknown payment, deadline, eligibility, contact, or stale evidence;
- `Brazil unavailable`: explicitly ineligible, still visible only when no filtering excludes it.

The HTML must visibly state the generation timestamp, applied filters, record count, and that the
briefing is evidence-based rather than a guarantee that an opportunity is valid or still open.

## Presentation and privacy rules

- Self-contained HTML/CSS/vanilla JavaScript only; add no frontend framework or runtime server.
- Use semantic HTML, responsive cards, readable typography, strong contrast, and no external CDN,
  analytics, fonts, trackers, or remote images.
- Local client-side source/domain/category text filters are allowed if they do not modify data.
- Escape every value rendered from source content. URLs must remain links, not injected markup.
- Generated `reports/*.html` is private output and must be ignored by Git.
- Never include raw payload JSON, credentials, tokens, browser paths, or hidden metadata in the
  HTML.

## Testing and documentation

- Keep rendering in a deterministic, offline-testable module, proposed path
  `src/global_builder_radar/briefing.py`.
- Add focused tests for: escaped hostile source text, all required card evidence/unknown states,
  factual grouping, enabled-source filtering, and no database mutation.
- Add the command to README and `docs/module-map.md`; record the unit in `CHANGELOG.md` and
  `docs/current-work.md`.
- Run `python -X utf8 -m pytest` and `python -X utf8 -m ruff check .`.

## Explicit non-goals

- No LLM/Gemini/Spark/Qwen API call or personal-profile inference in 4A.
- No tailored application text, email drafting, or automatic application/outreach.
- No lifecycle buttons, database writes, hosted domain, authentication, dashboard server, Sheets,
  Hermes, OmniRoute, or VPS work.

## Follow-on decision

After Everton uses the HTML briefing on real opportunities, decide separately whether to add:

1. small lifecycle commands (`shortlist`, `dismiss`, `actioned`); and/or
2. optional AI briefs backed by one explicitly selected provider, a truthful profile file, schema
   validation, caching, and a hard budget.

Neither follow-on is authorized by this contract.
