# Rite

Session discipline for Claude Code — enforced by checks that fail, not by conventions you have
to remember.

A session has two ends. At the start you need to know what state you are in and whose side a
problem is on. At the end you need what happened to survive the session that produced it. Rite
defines both, and defines what a project must carry so a cold agent can pick it up without
re-deriving it.

**Status:** `shipped`. An installed, running Claude Code plugin, tested on Linux, macOS and
Windows, published 2026-09-10. It has been used daily by its author since 2026-09-07 and by
nobody else, so treat the install instructions below as working but barely travelled.

## The problem

The raw record evaporates. Measured on the machine this was built on: four weeks of session
transcripts against ten months of `LOG.md`. Whatever is not distilled before a session ends is
gone — not archived, gone.

The usual answer is a rule: *"update the docs with current state."* That rule has no completion
test, so it fails quietly, and you find out months later when a document confidently describes
something that has not been true since July.

Templates are free and everyone has one. Almost nobody ships **the check that fails when you
don't follow it.** That check is the product.

## What it actually does

**At session start**, a hook runs the standard's checks and puts the verdict in Claude's
context — before you type anything:

```
rite — myproject

  NA     project  fresh      LOG.md        newest_entry_within_days_of_activity — documents-only project — no source to measure against
  NA     project  integrity  LOG.md        append_only_preserved — requires revision history — no git repository
  RED    project  integrity  HANDOFF.md    written_not_older_than_newest_log_entry — handoff written 2026-09-02, newest log entry 2026-09-10 — session did not close
  NA     project  populated  CONCERNS.yaml entry_required_keys — tier 2, not present — optional
  NA     project  —          46 checks not required at stage 'idea', waiting on:
                               spec     README.md, CLAUDE.md, docs/MISSION.md, docs/ROADMAP.yaml
                               build    docs/ARCHITECTURE.md, docs/CONVENTIONS.md, docs/DECISIONS.yaml
                               shipped  LICENSE

  61 checks · 1 RED · 0 YELLOW · 53 NA · 7 GREEN
  coverage: 57 of 64 declared tests implemented
  no git repository — integrity checks report NA (capability, not prerequisite)
```

Real output from a scaffolded project. Note the last block: checks your stage has not reached
are **collapsed and counted, never dropped** — you can see what is coming without being shown a
wall of things you have not done yet. And `coverage:` states what the checker itself cannot
verify, so the report is honest about its own limits rather than flattering.

Every finding says **whose side it is on** and what would clear it. A check the tool cannot run
reports `NA` and says so — it never quietly disappears, because a check that vanished and a
check that passed must not look alike.

**During the session**, `/rite:log` appends to `LOG.md`, reading the machine clock for every
entry so timestamps are real rather than extrapolated.

**At the end**, `/rite:end` does the judgement half while Claude still has turns: distil the
log, bring the documents back to true, close finished roadmap items, and record a handoff
decision. The next session's start-of-session check is what tells you whether you actually did
it.

## Install

Requires **Python 3**. That is the whole dependency list — there is nothing to `pip install`.

```bash
claude plugin marketplace add perieteanu/rite
claude plugin install rite@rite
```

Then, in a project you want to adopt it in:

```
/rite:init
```

That writes three files — `.rite.yaml`, `LOG.md`, `HANDOFF.md` — and the project scores **0 RED**
immediately. It never overwrites anything and is safe to re-run.

## It asks for very little at first

The `stage` line in `.rite.yaml` decides what the standard requires of you. A new project is
asked for two files, not thirteen:

<!-- rite:generated stage-table -->
| stage | what it adds |
|---|---|
| `idea` | `LOG.md`, `HANDOFF.md` |
| `spec` | `README.md`, `CLAUDE.md`, `docs/MISSION.md`, `docs/ROADMAP.yaml` |
| `build` | `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/DECISIONS.yaml` |
| `shipped` | `LICENSE` |
<!-- /rite:generated -->

Nothing expires and nothing nags. You raise the stage when the project genuinely changes, and
the checker then names exactly which documents it wants. A tool that opens by listing everything
you have not done yet gets uninstalled the next day.

**`/rite:init` deliberately seeds nothing beyond `idea`.** A log with one true entry is a
complete log and a "nothing to hand off" handoff is a complete handoff — but a `MISSION.md`
nobody has written is a lie that passes the file-exists check. Writing those stays your job.

Participation is opt-in and Rite is silent where it was not invited: no `.rite.yaml`, no output.

## What it costs you

```
Always-on:  ~354 tok   added to every session, for six skill descriptions
On invoke:  ~0.8-1.6k  each time a skill actually runs
Hooks:      0          harness-only; they never enter the model's context
```

Reproduce it with `claude plugin details rite`. That command is the honest answer; the block
above is a snapshot of it, and snapshots go stale.

## How it is built, which is the argument

The standard is a YAML document; the readable Markdown is **generated** from it, and a gate
fails if anyone hand-edits the generated copy. A standard that cannot catch its own drift has no
business asking that of anyone else.

<!-- rite:generated gate-counts -->
14 gates run on every push, across Linux, macOS and Windows. 4 cannot run on a CI runner — `test-riteyaml.py` (PyYAML is its oracle and CI does not install it), `test-preflight-port-parity.py` (a runner has no copy of preflight.py), `test-mirror-port-parity.py` (a runner has no copy of the script Rite ported from) and `test-installed-current.py` (a runner has no installed plugin) — so the runner reports **`10 of 14 gates ran`** and names the 4 it skipped rather than showing an unqualified green.
<!-- /rite:generated -->

The YAML is read by a subset parser shipped with Rite, so there is no dependency to install. It
**refuses rather than guesses** on anything outside the subset it was measured against, and its
correctness claim rests on a differential test against PyYAML rather than on a docstring.

## Honest limits

- **Claude Code only.** Not Cursor, not a generic "coding agent" abstraction. The enforcement
  Rite sells — a check that fires whether or not you remember to run it — exists only where the
  harness runs a `SessionStart` hook and reads its output.
- **The corpus proves the practice, not the design.** Twelve months and ~460 sessions show this
  practice was followed consistently. Nothing was tested against an alternative and no project
  deliberately went without, so this is a proven practice being distilled, not a validated
  theory.
- **Windows needs Git for Windows.** The hooks declare `shell: bash`, and without Git Bash the
  harness has no shell that can run them — a hook entry supports no per-platform conditional,
  so one command string must serve every platform and none does. Linux and macOS need nothing
  beyond Python 3.
- **The freshness windows are guesses** — 60 days for a roadmap, 90 for architecture — never
  calibrated against a real corpus. They are overridable per project, and an override is always
  reported alongside the default rather than applied silently.
- **One of the standard's declared rules is unimplemented** — `deleted_ids_appear_in_milestones`
  — and the report says so on every run instead of quietly scoring what it can. The coverage
  line reads `61 of 66` because its denominator counts test INSTANCES and includes four
  `optional` markers, which are not rules awaiting implementation
  (`c-coverage-counts-optional-as-unimplemented`).
- The `preflight.py` port and the continuous watcher layer do not exist.

Full list, including what is deliberately deferred and what will never be built:
[`docs/ROADMAP.yaml`](docs/ROADMAP.yaml) and [`docs/MISSION.md`](docs/MISSION.md).

## Reading further

| path | what |
|---|---|
| [`spec/PROJECT-STANDARD.md`](spec/PROJECT-STANDARD.md) | The standard, readable. **Generated** from the YAML beside it. |
| [`spec/SESSION-PROTOCOL.md`](spec/SESSION-PROTOCOL.md) | The session protocol, readable. Also generated. |
| [`docs/DECISIONS.yaml`](docs/DECISIONS.yaml) | Every settled decision and why, including the ones that were reversed. |
| [`LOG.md`](LOG.md) | What happened, in order. Published in full, including the mistakes. |

<!-- rite:claims
# Every path below is checked on every run — see claims_match_filesystem in the standard.
# The prose above is prose; these are the parts of it a machine can falsify. When a sentence
# here says a thing does not exist, name it, and the check fails the day that stops being true.
absent:
  - scripts/preflight.py
  - scripts/status.json
present:
  - .github/workflows
  - scripts/rite-check.py
  - scripts/rite_init.py
  - template/HANDOFF.md
  - skills/init/SKILL.md
  - hooks/hooks.json
  - .claude-plugin/plugin.json
  - LICENSE
-->

## Credits

Developed by Perieteanu Costin in collaboration with Claude (Anthropic's Claude Code).

## Unofficial

Not affiliated with, endorsed by, or sponsored by Anthropic. It contains no Anthropic code and
makes no API calls; it reads files that Claude Code writes on your own machine.
