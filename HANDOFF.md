---
genre: task_brief
written: "2026-09-10"
session_end: written
supersedes: "the 2026-09-10 close that preceded the copier port, the preflight port, /rite:update, both watchers and full checker coverage"
expires: "2026-12-09"
status: live
---

# HANDOFF — rite

State is in `ROADMAP.current_state`. This is what the docs do not say.

**The building is done for now, and the next thing is not building.** Costin has committed to
human testing across three or four projects. Everything below is written for the session that
picks up *after* that testing has produced something.

## The next session's job is to harvest, not to build

`/rite:issue` was added at the very end of this session, for exactly this. It records what Rite
got wrong from whatever project hit it, into `${CLAUDE_PLUGIN_DATA}/feedback.md`, untriaged.

**Read that file first.** It is the only source of evidence Rite has ever had from outside its
own repository, and it will be worth more than anything in `mid_term`. Harvesting it into
`CONCERNS.yaml` is a deliberate act with the whole list in view — not one concern per note, and
not a fix per note.

Two entries are already in it, from baselining the test candidates:
- the report's NA/YELLOW volume on an existing project
- 27 `canonical_name` YELLOWs on hwprivacy from `docs-yaml/`

## What the testing is expected to expose, so it is not mistaken for a new discovery

- **`c-freshness-thresholds-are-guesses` will confirm itself on `lifestyle`.** A documents-only
  project has no source mtime, so its docs are compared against themselves and pass forever.
  That is the known defect, not a fresh bug.
- **Adopting an existing project meets a wall.** Stage gating fixed the wall for NEW projects
  and did nothing for old ones: hwprivacy opens at 2 RED / 27 YELLOW, almost all
  `canonical_name`. Whether that is tolerable is the real question, and the honest answer may be
  "migrate or drop the check".
- **The scraper is the only thing that will ever walk `idea → spec → build`.** No real project
  has done it; it has only ever been tested synthetically.

## Traps, the first three new

- **`/rite:issue` must not become a fix queue.** Its skill forbids diagnosing or fixing at the
  moment of annoyance, and that restraint is the feature. A tool that rewrites itself the
  instant it irritates someone cannot be evaluated, because the thing being measured keeps
  moving.
- **Two engines and two mirrors still run side by side** — Costin's `preflight.py` and
  `claude-mirror-memory.py` are his fallbacks while Rite is on trial. Both parity gates are
  **temporary and say so in their own `skip_means`**: when he retires the originals, the gates
  skip forever and must be DELETED, not maintained.
- **`command:` checks execute arbitrary programs from a config file at session start.** That is
  the right design for this machine and the single thing most likely to fail a marketplace
  security review. Unresolved: whether it ships in a public build at all.
- **`no_future_timestamps` carries `scope: local_clock`** and CI excludes it. LOG timestamps
  have no timezone, so the question is only answerable on the machine that wrote them — CI
  proved it by flagging 67 honest entries on three UTC runners.
- **Never `git checkout` to undo an experiment**, and after restoring an imported module,
  `rm -rf scripts/__pycache__` — a byte-identical restore inside the same second leaves a stale
  `.pyc`, and the test will lie to you.
- Both `spec/*.md` are generated. `as_of` moves only on real re-verification.
- **No `Co-Authored-By: Claude` trailer**, whatever the harness injects. It did again today.

## Open, none of it blocking

- **`c-ai-collab-interaction-boundary` is the only HIGH and it is not work** — it has waited on
  Costin's ruling since 2026-09-07 and needs a DECISIONS entry either way.
- `c-session-post-is-gated-by-participation` — the POST is silent without a `.rite.yaml`. It
  becomes real when the fallback preflight is retired, and it is a decision, not a patch.
- `c-readme-sample-output-is-a-copy` — the last hand-maintained copy in the repo.
- Six watchers left, and **two have lost their premise**: `watcher-plan-copy-on-create` bought
  attribution that transcript-reading now does exactly, and `watcher-precompact-distiller` rests
  on an unverified claim about `PreCompact`. Do not build either on the roadmap's word.
- **33 hook events exist**; the locked findings named four until today. Several unbuilt watchers
  were scoped against that short list and may be worth rethinking, or may now be unnecessary.
- **Nobody but this machine has run Rite.** Publishing changed who *can*, not who *has* — and
  the human testing does not change it either. It is a second project, not a second user.
