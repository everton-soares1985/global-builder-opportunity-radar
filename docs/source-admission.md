# Source admission standard

A source is enabled by default only after passing this evidence gate.

## 1. Relevance

- It regularly publishes freelance, project, bounty, grant, hackathon, fellowship, or paid-program
  opportunities.
- Traditional jobs can be removed reliably before persistence or marked outside the primary feed.
- The opportunity is actionable by an individual developer or small team.
- Marketing, sales, or operations listings require a defined paid project/contract deliverable or
  a clear automation component; generic permanent management roles do not qualify.

## 2. Access method

Use the least fragile method that supplies sufficient evidence:

1. official public API;
2. RSS or Atom;
3. public JSON or structured page data;
4. public HTML with Scrapling;
5. Apify Actor when cloud execution, proxying, or an existing maintained Actor provides measurable
   value.

Document authentication, rate limits, pagination, and terms relevant to implementation. Paid
access must be optional, disabled by default, and budget-limited.

## 3. Evidence quality

Every accepted item needs:

- stable source and external identity;
- original public URL;
- title and enough description to evaluate the work;
- opportunity category;
- raw evidence required to reproduce parsed fields;
- collection timestamp;
- compensation and deadline as parsed evidence or `null`, never guesses.

## 4. Eligibility and safety

Extract or classify when available:

- country/region restrictions;
- Brazil eligibility: `eligible`, `ineligible`, or `unknown`;
- payment method and currency;
- application fee, deposit, wallet, credential, or private-key requests;
- suspicious redirects, impersonation, and unverifiable contacts.

Safety signals inform review. They do not become accusations or blacklists without evidence.

## 5. Reliability

- Parser logic has sanitized offline fixtures.
- Pagination and empty states are tested.
- A source failure returns a failed `CollectionResult` without stopping the batch.
- Health output distinguishes zero real results from extraction failure.
- Duplicate identities remain stable across repeated runs.
- The live smoke test records real counts and source evidence.

## 6. Confidence lifecycle

| State | Meaning | Default enabled |
|---|---|---|
| `candidate` | Researched but not implemented. | No |
| `experimental` | Real data observed; parser or semantics still unstable. | Only for supervised runs |
| `verified` | Fixtures, live smoke test, evidence fields, and health behavior pass. | Yes |
| `degraded` | Previously verified but current extraction is unreliable. | No |
| `retired` | Source removed or no longer relevant. | No |

Update `docs/sources.md` whenever confidence changes.

## Definition of done for a collector

- source record and rationale documented;
- config entry disabled during development;
- collector isolated and registered;
- normalized fields and provenance preserved;
- fixtures and tests green;
- live smoke test successful;
- malformed, empty, duplicate, and restricted cases handled;
- `health` output truthful;
- enabled only after the evidence above is recorded.
