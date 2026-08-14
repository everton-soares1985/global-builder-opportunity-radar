# Autonomous agent runbook

## Session start

Open PowerShell in the repository root, then run:

```powershell
.\.venv\Scripts\Activate.ps1
git status --short
git branch --show-current
python -X utf8 -m pytest
python -X utf8 -m ruff check .
```

Then read the mandatory documents listed in `AGENTS.md` and inspect only the modules related to the
selected roadmap phase.

`docs/current-work.md` identifies the single work unit to execute. Do not select a later unit merely
because it looks easier.

## Work-unit template

Before coding, write this short internal contract:

```text
Roadmap phase:
User outcome:
Files expected to change:
Acceptance criteria:
Tests to add or update:
Live validation, if any:
Explicit non-goals:
```

Keep one work unit small enough to review as a coherent diff.

If another coding window is active, use a separate Git worktree and branch. Two writable agents
must never share the same working directory or edit the same work unit concurrently.

## During implementation

- Preserve existing behavior unless the roadmap explicitly changes it.
- Prefer pure parser functions that can be tested without the network.
- Do not mix collection, ranking, persistence, UI, or integrations in one module.
- Record uncertain source facts as unknown, not inferred truths.
- Do not conceal degraded collectors behind empty successful results.

## Session finish

Run the validation gates from `AGENTS.md`, then report:

```text
Completed:
Evidence/tests:
Live source result:
Files changed:
Documentation updated:
Wiki cards created/updated or service unavailable:
Remaining risks:
Next roadmap item:
Commit/push status:
```

Do not claim completion when a required gate is red.

## Wiki/Knowledge bootstrap

When the IDE knowledge service is available, build the Wiki yourself:

1. Create cards named `GBR — Mission`, `GBR — Architecture`, `GBR — Module Map`,
   `GBR — Source Admission`, `GBR — Current Sources`, and `GBR — Roadmap`.
2. Summarize the matching canonical document without copying secrets or personal data.
3. Include the repository-relative canonical path and its last reviewed date.
4. Add module-specific cards only when a module becomes too complex for `docs/module-map.md`.
5. Refresh cards whenever their canonical document changes.
6. If the service is unavailable, do not create an alternative proprietary store; keep `docs/`
   current and try again in a later session.
