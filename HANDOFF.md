---
genre: task_brief
written: "2026-09-12"
session_end: written
supersedes: "the 2026-09-10 close, which handed off to human testing that had not yet started"
expires: "2026-12-11"
status: live
---

# HANDOFF — rite

State is in `ROADMAP.current_state`, corrected against the host today. This is what the docs do
not say.

**The next thing is testing, and it starts with a restart.** Two plugin updates landed today and
both printed *"Restart to apply changes"*. A session that has not restarted since is exercising
the OLD hooks — so the write-time YAML watcher and the new freshness rules would not be what a
test measured. Reload first, then adopt.

## Testing another project: what the session before you learned the hard way

- **Start a NEW session in the other project. Do not `cd`.** Rite assumes one project per session
  and resolves `LOG.md`, `HANDOFF.md` and every copy destination from one root;
  `watcher-cwd-changed` reports the move once, which is a warning and not a fix.
- **Preview read-only before adopting**: `rite.sh check <path> --force` scores a project with no
  marker and writes nothing.
- **Write two or three predictions before the first run.** This project's record keeps earning it:
  "hwprivacy near-clean, 2-4 findings" turned out to be 17, and today's parser work was decided by
  probing PyYAML rather than by reading code. A vague expectation gets scored as correct afterwards.
- **Expect `yaml_parses` REDs immediately.** 22 YAML files on this machine are invalid right now,
  across ten projects. Those are true findings about the documents, not Rite misbehaving.
- **Expect the `docs-yaml/` wall on an existing project** — hwprivacy opens at 2 RED / 27 YELLOW,
  plumbing at 1 RED / 23 YELLOW, almost all `canonical_name`. Whether that is tolerable or whether
  the check should be dropped is STILL the real unknown, unchanged since 2026-09-10.
- **`/rite:issue` captures; do not fix Rite mid-test.** A tool that rewrites itself the instant it
  annoys someone cannot be evaluated, because the thing being measured keeps moving.
- **Field notes go in `tests/<name>/`** — gitignored and never committed
  (`d-tests-folders-never-committed`), harvested into `CONCERNS.yaml`, then deleted.

## Traps, two of them mine from today

- **An `Edit` aimed at the wrong anchor modified a committed entry in an append-only file**, and
  the decision it was meant to add went nowhere — leaving four documents citing an id that did not
  exist. Nothing caught it; reading the tool result did. Verify an append landed where you meant.
- **A generated block can rewrite itself.** The README sample's first fixture carried an expiry in
  the past, so the output held a day count measured from today. Two `--check` runs passed and
  proved nothing, because they ran in the same minute.
- **Running the gates from a `git worktree` can silently downgrade one to SKIP** —
  mirror-port-parity resolves state from the path-derived project slug. Verify in the main tree.
- **`spec/` is not compared by `test-installed-current.py`**, so the installed plugin's copy of the
  standard can drift from the repository while the gate stays green — and the running checker reads
  the installed one. That is `c-installed-spec-is-not-compared`.

## Open, and the two cheapest next

- **`c-installed-spec-is-not-compared`** — plausibly one line in `COMPARED` plus a test, and today's
  own reinstall is what exposed it.
- **`c-commit-is-not-gated`** — worth having now in a way it was not yesterday: `yaml_parses` gives
  a pre-commit gate something real to catch. Its edge cases are already written down there, including
  that the gate must run with `--exclude-scope=session`.
- Also open: `c-yaml-values-are-misread-in-ways-that-still-parse` (three block literals undiagnosed),
  `c-copier-ignores-the-project-it-writes-into`, `c-memory-has-no-cross-project-lane`,
  `c-roadmap-vocabulary-assumes-building`, and `c-ai-collab-interaction-boundary`, which has waited
  on a ruling since 2026-09-07 and is not work.

## Do not re-litigate

Settled today, with measurements and tests behind both: what a YAML refusal MEANS (two kinds, and
the subset is declared in the spec), and what "source" means for freshness (recorded change, never
file timestamps). Both have their reasoning in `DECISIONS.yaml` and their evidence in `LOG.md`.
