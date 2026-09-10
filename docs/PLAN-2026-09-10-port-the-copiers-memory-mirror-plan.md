<!-- Copied from ~/.claude/plans/calm-tinkering-kahan.md on 2026-09-10.
     Plans are written outside the project under harness-generated names carrying no
     project attribution; they are lost when the session ends unless copied. Canonical
     name per spec/project-standard.yaml artifact `plan_copy`. Copied by rite_copy.py,
     which attributes a plan to the project whose SESSION wrote it. -->

# Port the copiers: memory mirror, plan copy, script copy

## Context

`port-mirror-memory` sits in `ROADMAP.mid_term` with the note *"Plans are the identical problem
with a different source dir. One tool, not two."* That instinct is right, and the request extends
it to a third source: the helper scripts Claude writes to the scratchpad during a session, which
vanish when the session ends and take the reproducibility of the commit with them (15 of them
today produced four commits).

Three findings from exploration reshape the work:

1. **`c-plan-attribution` is not hard.** It is recorded as *"the only genuinely hard part"*,
   blocking `port-mirror-memory`, and it proposes "mtime/session correlation or content
   inspection". Neither is needed. Session transcripts live at
   `~/.claude/projects/<slug>/*.jsonl` and **contain the plan's absolute path literally**.
   Measured: **13 of 13 plans on this machine attribute exactly**, to rite, hwprivacy, tattvas,
   claude-persistent and ccrm. Two resolve through a `subagents/` subdirectory and need one hop
   up to the slug. This is evidence, not heuristics — which is the difference between a copier
   this project can ship and one it would have to hedge.
2. **Script copy needs no attribution at all.** The scratchpad is
   `/tmp/claude-<uid>/<slug>/<session-uuid>/scratchpad/`. The slug is in the path.
3. **`c-pattern-paths-are-matched-literally` is a prerequisite, not a neighbour.** `plan_copy`
   declares `path: "docs/PLAN-YYYY-MM-DD-<slug>.md"` and `rite-check.py:831` computes presence
   with `ctx.exists_exactly(art["path"])`. Until that is fixed, both tests this port exists to
   implement — `filename_matches_canonical` and `source_plans_all_copied` — report "not present"
   no matter what is on disk.

Outcome: one module, three copiers, a shared spine. Three of the seven unimplemented tests get
implementations, and `c-plan-attribution` is settled by a measurement rather than deferred again.

---

## Stage 0 — Make a pattern path matchable (prerequisite)

- Add an optional `path_pattern` (glob) beside `path` in the artifact schema,
  `spec/project-standard.yaml`. `path` stays the canonical *display* name.
- In `scripts/rite-check.py`, presence becomes a glob match when `path_pattern` is set,
  literal `exists_exactly` otherwise. Keep `exists_exactly` for the literal case — it exists
  because macOS and Windows are case-insensitive and must not give a second verdict.
- `plan_copy` declares `path_pattern: "docs/PLAN-*.md"`. `filename_matches_canonical` then has
  something to check: every file matching the glob must also match `PLAN-<ISO>-<kebab>.md`.
- Retire `c-pattern-paths-are-matched-literally` with a DECISIONS entry.

**Stop-and-check:** with two plan files already on disk, the checker must stop saying
"not present". That is the whole test for this stage.

## Stage 1 — The spine and the attributor

New `scripts/rite_copy.py`. One module, three copiers, because the differences are data:

| copier | source | destination | cardinality | discipline |
|---|---|---|---|---|
| memory | `~/.claude/projects/<slug>/memory/*.md` | `docs/claude-memory.md` | one file | `free_replace` |
| plans | `~/.claude/plans/*.md` | `docs/PLAN-<ISO>-<slug>.md` | many | `write_once` |
| scripts | `/tmp/claude-<uid>/<slug>/<uuid>/scratchpad/*` | `docs/session-scripts/<ISO>/<name>` | many | `write_once` |

Cardinality follows write discipline, and the spec already states the rule in
`memory_mirror.structure.why_single_file`: `free_replace` → one file, `write_once` → many. The
spine is four operations — `sources()`, `attribute()`, `destination()`, `write()` — plus one
reporter. Reuse `ritefs.use_utf8_stdio()`, `ritefs.exists_exactly()` and `riteyaml` rather than
adding helpers.

**The attributor is the piece worth building carefully.** `attribute(path) -> slug | None`:
scan `~/.claude/projects/**/*.jsonl` for the source file's absolute path; walk up to the
`projects/<slug>` level so a `subagents/` hit resolves correctly; map slug → project root by
reversing the slug derivation (`claude_home_slug_derivation` is already a declared portability
rule in the spec — read it, do not re-invent it).

**It must refuse rather than guess**, exactly as `riteyaml` does: a plan matching no transcript
is reported unattributable and skipped, never placed by mtime proximity.

## Stage 2 — Plan copy

- `write_once` means the destination is never overwritten. An existing `PLAN-*.md` is skipped
  and counted, not diffed.
- Implements `source_plans_all_copied`: a plan attributable to this project with no copy here
  fails the check.
- **Backfill writes into rite only.** The other seven plans are reported with the project they
  belong to and nothing is written outside this repo — `ROADMAP.deferred_deliberately` says
  migrating other projects is separate and opt-in, and a tool that writes into repositories you
  did not open is the wrong first impression.

## Stage 3 — Memory mirror

Port `~/.claude/scripts/claude-mirror-memory.py` (367 lines). Keep the output contract
byte-compatible — `generator-signature: claude-mirror-memory/v1`, the `Last sync` line, the
"N memories (MEMORY.md index excluded)" count — so the existing `docs/claude-memory.md` does not
churn and `mirror_not_stale` has a stable thing to read.

Drop on the way over: the `importlib` load of `claude-global-audit.py` for `registered_roots`.
That reaches into the portfolio registry, which Rite does not own
(`d-project-tracker-stays-separate`). Rite's `--all` walks `~/.claude/projects/*/memory/` and
maps slug → root with its own attributor.

**Coexistence, deliberately boring:** `~/.claude/settings.json` registers the global script on
`SessionStart` and `PostToolUse` (lines 462, 477, 489). **Leave it running.** Rite's port is
proven side by side first; retiring the global hook is a separate, reversible step and not part
of this work. Two writers producing identical bytes is safe; swapping them mid-port is not.

## Stage 4 — Script copy (a new artifact, so a new decision)

- **This is the 14th artifact and the inventory is frozen at 13.** `CLAUDE.md` says a 14th
  requires a DECISIONS entry, and that script-produced files are outside the freeze only until
  their producers exist — this commit builds the producer, so write the entry.
- Destination `docs/session-scripts/<ISO date>/<name>`, grouped by date rather than flat:
  today alone produced 15 files, and 15 × sessions in `docs/` would drown the documents.
- Copy `*.py` and `*.sh` from the scratchpad root only. Skip `*.bak`, skip directories — today's
  scratchpad holds `README.md.bak` and a `shipped-probe/` tree, neither of which is a script.
- Runs from `/rite:end` and from `rite_session_end.py`: the scratchpad lives in `/tmp` and does
  not survive a reboot, so late is the same as never.

## Wiring

- `hooks/rite.sh` and `rite.ps1` gain a `copy` action, using the explicit action table added
  today. Both shims change identically.
- `rite_session_end.py` calls the mechanical copiers (plans, scripts). No judgement involved.
- `skills/end/SKILL.md` gains a step naming what was copied.
- Register the new tests in `.github/gates.yaml`.

---

## Verification

Each stage has one claim that can fail, and none of them is "it ran":

- **Stage 0:** `rite-check.py` currently prints `docs/PLAN-YYYY-MM-DD-<slug>.md ... not present`
  with two plan files on disk. After: it finds them. Run it before to capture the wrong output.
- **Stage 1:** the attributor reproduces the measured result — **13/13 plans attributed**, with
  `hwprivacy-camera-sessions.md` and `hwprivacy-pw-dump-monitor.md` resolving through
  `subagents/` to hwprivacy. A plan file with a fabricated name must come back *unattributable*,
  not guessed.
- **Stage 2:** backfill writes 6 plans into `rite/docs/`, reports 7 elsewhere, and **writes
  nothing outside this repo** — verify with `git status` in the other projects, not by reading
  the tool's own summary.
- **Stage 3:** regenerate `docs/claude-memory.md` with the port and diff against the file the
  global script produced. **Byte-identical except the timestamp**, or the port is not a port.
- **Stage 4:** a second run copies nothing new (`write_once` holds), and `*.bak` and
  `shipped-probe/` are absent from the destination.
- **All stages:** `python3 .github/run-gates.py` green, and each new gate proved to FAIL before
  being trusted — break it, watch it fail, restore from a file copy, never `git checkout`.

## Not doing

- **Not retiring the global mirror hook** in `~/.claude/settings.json`. Separate, reversible,
  after the port is proven. (Noted in passing: those three hook commands hardcode `python3`,
  which is the rule fixed in rite today. Costin's global config, not this repo's.)
- **Not writing into hwprivacy, tattvas, claude-persistent or ccrm.**
- **Not building `watcher-plan-copy-on-create`.** Copy-at-creation via `FileChanged` is a
  separate roadmap item and its premise — that `FileChanged` watches paths outside the project
  root — is still unverified. Transcript attribution makes it an optimisation now, not a
  prerequisite.
- **Not touching `ai-collab-profile/`, `prompts.db`, or `prompts-corpus.jsonl`** — permanently
  out of scope. Transcripts are read only to resolve a plan's project, never for content.
- Not porting `preflight.py` or `hookdedup.py` (`port-preflight`, a separate item).
- Not implementing the remaining four unimplemented tests.
