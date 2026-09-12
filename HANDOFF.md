---
genre: task_brief
written: "2026-09-12"
session_end: written
supersedes: "the 2026-09-12 morning close, which handed off to testing — the testing happened"
expires: "2026-12-11"
status: live
---

# HANDOFF — rite

State is in `ROADMAP.current_state`, rewritten against the host today. This is what the docs do
not say.

## The one thing to verify first, because this session could not

**The resolver injection has never actually run.** `/rite:end` was invoked at the close of this
session and the harness handed over the **pre-edit skill body** — no `## This project, resolved`
block, no `!` command. The plugin had updated to 0.25.0 mid-session and printed *"Restart to
apply changes"*, so the session was still running the old prompt. The step was performed by
hand instead.

So `rite_paths.py` is tested, and the five SKILL.md files are edited and gated, but the
**delivery path between them is unexercised**. Restart, run `/rite:end` or `/rite:log` in this
project, and confirm the resolved block actually appears above the steps. If it does not,
dynamic context injection is not doing what the documentation says, and two concerns retired
today were retired on an untested mechanism.

The previous handoff opened with the same warning about the same trap. It was right, and it
still got us.

## What is built but has no user

- **`legacy_layout` has never been declared by a real project.** Every measurement came from a
  fixture. hwprivacy still carries no `.rite.yaml` at all, so adopting it is the obvious next
  test — and it is the project the feature was designed from.
- **`rite.sh paths` is new.** It is the first action added since the port, and the only one the
  skills depend on rather than the hooks.

## Open, and what each is waiting on

- **`c-watcher-cannot-see-shell-writes`** (high) is the biggest hole and is NOT blocked on
  effort — it is blocked on one lookup. The proposal rests on `FileChanged` firing for writes
  made by a Bash call, which nobody has verified. Read the hooks reference before designing
  against it; this project has already scoped a watcher layer against a list of four events when
  thirty-three exist.
- **`c-session-post-is-gated-by-participation`** needs a RULING, not code, and its `do_not` says
  so. The question sharpened today: does participation distinguish a hook firing unbidden from a
  CLI invoked by name? `/rite:end` now *reports* the silence, but the tools are still silent.
- **`c-copier-has-no-read-only-preview`** — `check` has `--force`, `copy` has none, and the
  copier is the one with files at stake. The constraint is recorded: on a writer that flag can
  only mean preview, never write.

## Bookkeeping nobody has ruled on

- **Three concerns sit in BOTH `concerns` and `retired_ids`** — `c-source-is-filesystem-mtime`,
  `c-project-yaml-is-not-checked`, `c-readme-sample-output-is-a-copy`. All three are
  `status: settled` and were marked done in place rather than moved, which is what the file's own
  lifecycle forbids and what `unique_ids` cannot see, since it only checks within `concerns`.
  Raised twice today and deliberately not fixed: it is a decision about someone else's
  bookkeeping, not a defect to quietly tidy.
- **`tests/hwprivacy/` is harvested and can go.** The convention is harvest into `CONCERNS.yaml`
  then delete. Everything in it is now either a concern, a decision, or a correction recorded
  against it. It is gitignored, so nothing depends on the timing.

## Traps this session paid for

- **A measurement contaminated by its own harness.** Parking the marker as `off.yaml` INSIDE the
  fixture made a stray root-level YAML count as source, so the baseline described a different
  project and an unexplained verdict change appeared. Move the file OUT of the tree. This is the
  second time the act of measuring changed what was measured; the first was plan attribution.
- **Totals hide the wrong kind of improvement.** The first `legacy_layout` build destroyed three
  true GREENs while the summary line looked better. Diff the verdicts line by line; comparing
  `checks · RED · YELLOW` tells you nothing about which findings moved.
- **A finding can be confidently wrong about its own cause.** The corpus blamed `DOCS = "docs"`
  for a silent copy; the participation gate returns first and that line is never reached. Both
  were real bugs, but fixing the named one would have changed nothing about the reported symptom.

## Do not re-litigate

Settled today, with tests behind both: a legacy layout is a DECLARATION that suppresses layout
findings only and reports itself once (`migrate_by` optional, by Costin's ruling), and no
documentation path is written as a literal. Reasoning in `DECISIONS.yaml`, evidence in `LOG.md`.
