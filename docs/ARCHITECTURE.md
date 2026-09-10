---
schema_version: "1.0.0"
as_of: "2026-09-10"
status: current
# The file tree below is a claim about the repository, and this is the falsifiable half of it.
# ARCHITECTURE is must_be_current and rotted hardest: on 2026-09-08 it omitted the checker
# entirely, and on 2026-09-09 it still called the session-start script "planned", said it
# writes status.json, and said it reads an /end stamp file that had been REJECTED.
claims:
  absent:
    - scripts/preflight.py
    - scripts/status.json
  present:
    - .github/workflows/gates.yml
    - .github/gates.yaml
    - .github/run-gates.py
    - scripts/rite-check.py
    - scripts/riteyaml.py
    - scripts/ritefs.py
    - scripts/rite_session_start.py
    - scripts/rite_session_end.py
    - hooks/hooks.json
    - hooks/rite.sh
    - hooks/rite.ps1
---

# ARCHITECTURE — rite

*What lives where, what flows where, who owns what. Read this second, after MISSION.md.*

## Shape

Rite is ONE Claude Code plugin. A plugin cannot draw UI — that is a hard API fact, not a
limitation to engineer around — so the persistent surface stays an optional, separate VS Code
extension that ships later and is never required.

```
SessionStart hook ──► preflight checks ──► verdict + what the last session left open
                                                  │
PostToolUse hook  ──► mirror agent memory into the repo
                                                  │
/end command      ──► JUDGEMENT half: LOG entry, docs update, handoff
(user-invoked, while Claude still has turns)       │   └─ records `session_end:` in HANDOFF front matter
                                                  ▼
SessionEnd hook   ──► MECHANICAL half: copy plans, mirror memory
                      (no stamp file — see below)
                                                  │
                                                  ▼
                      next SessionStart compares HANDOFF `written:`
                      against the newest LOG.md entry, and says what you skipped
```

The loop closes at the next session start. **That is the completion test.**

**There is no stamp file.** An earlier version of this diagram had `SessionEnd` writing one;
`d-end-outcome-recorded-in-handoff` rejected it. `/end` is a process and its result belongs in
the artifact the process is about, so it goes in `HANDOFF.md` front matter as
`session_end: written | updated | carried_forward | none`.

That leaves the detection question, which the stamp was there to answer: a session that worked
and then closed without touching the handoff leaves `written:` **older than the newest `LOG.md`
entry**. Two Tier 0 files that already exist, no third artifact, and checkable today without
revision history.

## Layout

```
spec/
  project-standard.yaml   The standard, machine form. AUTHORITATIVE.
  PROJECT-STANDARD.md     Same content, readable. GENERATED — never hand-edit.
  session-protocol.yaml   The protocol, machine form. AUTHORITATIVE.
  SESSION-PROTOCOL.md     Same content, readable. GENERATED — never hand-edit.
  render-standard.py      Generator + drift gate for BOTH (--check, --protocol --check).
docs/
  MISSION.md              prose        · rewrite-only
  ARCHITECTURE.md         prose        · rewrite-only, must always be current
  CONVENTIONS.md          prose        · rewrite-only
  DECISIONS.yaml          structured   · append-only
  ROADMAP.yaml            structured   · MIXED — body rewrite-only, milestones append-only
  CONCERNS.yaml           structured   · MIXED — entries mutate, retired_ids append-only
  PLAN-<date>-<slug>.md   prose        · write-once
```

Root: `README.md` and `CLAUDE.md` (rewrite-only), `LOG.md` (append-only), `HANDOFF.md`
(write-once, tier 0 — always present, `genre: none` when there is nothing to hand off).

Built, as of 2026-09-10:

```
scripts/
  rite-check.py      THE CHECKER. Reads spec/project-standard.yaml and runs the completion
                     tests. 61 checks on this project; 57 of 64 declared tests implemented.
  riteyaml.py        Stdlib-only parser for the YAML subset this project uses. 358 lines.
                     REFUSES rather than guesses on anything outside the subset.
  test-riteyaml.py   Differential test against PyYAML as ORACLE, not dependency.
  ritefs.py          Case-exact filesystem predicates. ONE implementation of
                     case_sensitive_name_matching; rite-check and both hooks route through it.
  test-hook-output.py  Contract test: the SessionStart hook's stdout must nest its verdict
                     under hookSpecificOutput. Asserts SHAPE, not content — see below.
  test-checker-verdicts.py  The checker's own test: unparseable is RED, absent stays NA, a
                     broken marker is reported, and a false claim is caught.
  test-installed-current.py  Contract test: the INSTALLED copy must match this working tree,
                     by version and by content. Skips where Rite is not installed.
.rite.yaml           The opt-in marker. Presence is the signal; empty would be valid.
```

CI, as of 2026-09-10 — the gates stop depending on someone remembering:

```
.github/
  workflows/gates.yml  push to main, pull_request, workflow_dispatch. ubuntu-latest only.
  gates.yaml           THE GATE LIST — id, command, and what a skip means. The single home
                       for it; this document describes the gates, it does not define them.
  run-gates.py         Runs each gate and distinguishes 0 pass / 1 fail / 2 SKIP. Reads the
                       list with scripts/riteyaml.py, so CI exercises Rite's own parser.
```

**A skip is never folded into green.** Two gates cannot run on a runner — `test-riteyaml.py`
(PyYAML is its oracle and CI does not install it) and `test-installed-current.py` (a runner has
no installed plugin) — so the runner prints `5 of 7 gates ran` and names what was not enforced.
That is `rite-check.py`'s own *NA, never silence* rule applied one level up, to the gates
instead of to the checks. A gate exiting 2 without declaring `skip_means` is treated as a
FAILURE, because an undeclared skip that reads as success is the exact shape of the problem.
`.github/` sits outside the four paths `test-installed-current.py` compares, so CI plumbing
never forces a plugin version bump. See `d-ci-reports-its-own-coverage`.

The plugin, as of 2026-09-08 — **the repo root IS the plugin**:

```
.claude-plugin/
  plugin.json        name, version, description, author, license
  marketplace.json   advertises this repo as a one-plugin marketplace
skills/              /rite:log /rite:end /rite:handoff /rite:preflight
  log/SKILL.md         both-invocable — Claude logs as work happens
  end/SKILL.md         disable-model-invocation: Claude never ends a session
  handoff/SKILL.md     disable-model-invocation
  preflight/SKILL.md   user-invocable
hooks/
  hooks.json         SessionStart (startup + resume), SessionEnd
  rite.sh            POSIX launcher shim — finds an interpreter or explains why not
  rite.ps1           the same, for Windows without Git Bash
scripts/
  rite_session_start.py   verdict + did-the-last-session-close + handoff state
  rite_session_end.py     mechanical close
```

Still planned, not built:

```
hooks/            PostToolUse — belongs to port-mirror-memory (see below)
scripts/          preflight.py port — port-preflight
```

**The hook's output shape is a contract, not a detail.** The harness reads
`hookSpecificOutput.additionalContext`; a top-level `additionalContext` is ignored while the
hook is still logged as `success`. On 2026-09-08 Rite's first live SessionStart did exactly
that — ran, exited 0, emitted valid JSON, reached nobody. `scripts/test-hook-output.py` pins
the shape so it cannot silently regress. See `d-hook-output-shape-is-a-contract`.

**A local-path plugin is only as current as its last version bump.** The install cache is a
real copy of the repo, and `claude plugin update` is version-gated: editing a source file
changes nothing until `.claude-plugin/plugin.json` gets a new version. What runs is the last
installed version, never the working tree. `scripts/test-installed-current.py` enforces this;
see `d-installed-copy-checked-by-test-not-by-rule` for why it is a test and not a checker rule.

**The YAML subset was widened on 2026-09-09** after the first run against outside projects
found block literals and flow mappings in real files. `riteyaml.py` now covers those, plus
chomping indicators and multi-line plain scalars, and still refuses anchors, aliases, tags,
merge keys and complex keys. Stdlib only; PyYAML remains the test oracle and is imported
nowhere. See the `widened_2026_09_09` block inside `d-stdlib-only-yaml-subset`.

**`PostToolUse` is deliberately absent.** The obvious implementation calls
`~/.claude/scripts/claude-mirror-memory.py`, which is Costin's script, not Rite's — a plugin
hook depending on a file only one machine has is broken by design for everyone else, and on
this machine it would double-fire against the entry already in `settings.json`. It lands with
`port-mirror-memory`.

**`/next` is deliberately absent.** It writes to `next-steps.yaml`, which belongs to
project-tracker — `d-project-tracker-stays-separate` and the standing don't-claim rule both
forbid Rite owning it. It was listed here in error until 2026-09-08.

## Format split

The docs directory is deliberately mixed, and the rule is **each file pays for what it is**:

| form | files | why |
|---|---|---|
| Markdown + YAML frontmatter | MISSION, ARCHITECTURE, CONVENTIONS, HANDOFF, PLAN | Prose. Measured on this project's own spec — identical content cost 25287 bytes as YAML and 19275 as Markdown, a 24% saving, because YAML charges a `key:` and an indent for every line of paragraph. Markdown also needs no parser and cannot fail to load on a bad indent. |
| YAML | DECISIONS, ROADMAP | Real structure — repeated entries with fields the completion tests read (`unique_ids`, `no_dangling_supersedes`, `entry_required_keys`, `min_list_items`). PyYAML is already present; hand-writing a Markdown-structure parser to replace it would trade a good dependency for a worse one. |

The provenance header (`schema_version`, `as_of`, `status`) is identical in both: YAML
frontmatter in a `.md`, top-level keys in a `.yaml`. One parser reads both.

Write discipline is the second axis and is independent of form — a `.md` can be append-only
(`LOG.md`) and a `.yaml` can be mixed (`ROADMAP.yaml`). Form answers *how it is encoded*;
write discipline answers *how it may legally change*. Both are declared per artifact in the
spec; the full table is in CONVENTIONS.md.

The directory is named `docs/`, not `docs-yaml/`, precisely so the name never has to change
again when a file changes form.

## The shim boundary

Everything Rite does is Python, written once. The single exception is a launcher shim, whose
only job is to find an interpreter or explain that it cannot.

```
hook ──► sh -c        (Linux, macOS)          ──┐
    ──► Git Bash     (Windows, recommended)   ──┤► shim ──► python3/python/py ──► Python
    ──► PowerShell   (Windows, no Git Bash)   ──┘   │
                                                   └─ not found ──► "Python 3 required: …", exit 1
```

**Two shims: `.sh` and `.ps1`. Never `.bat`.** Verified against the hooks documentation, not
assumed: a hook's `shell` field accepts `bash` or `powershell` and *"defaults to bash, or to
powershell on Windows when Git Bash isn't installed"*. `cmd.exe` plays no part in hook
execution on any configuration, so a `.bat` would be dead code.

Exec form — setting `args` — bypasses the shell entirely on every platform, and would remove
the Git Bash quirks below. It does not remove the need for a shim: it requires a concrete
executable name, and none works everywhere (macOS has `python3` but not `python`, Windows has
`python` and `py` but often not `python3`).

The two shims cannot meaningfully drift: each has one job, contains no check, parse or logic,
and PowerShell is a real language, so the `.ps1` is a translation rather than a
reimplementation.

Windows traps when the path runs through Git Bash: it consumes unquoted backslashes, it
auto-aliases `node` to `winpty node.exe`, and `CLAUDE_CODE_GIT_BASH_PATH` may relocate it —
never hardcode its path.

**Still unverified:** none of this has run on a real Windows or macOS machine. Documentation
plus binary strings is better than assumption and worse than a test.

## Hard boundaries

- **judgement_vs_mechanical** — `SessionEnd` fires when Claude has no turns left. It can copy
  files and stamp state; it CANNOT write a handoff, distill a LOG entry, or update docs.
  Anything needing judgement runs earlier, from a user-invoked command. This split is forced
  by the harness, not chosen.
- **never_mutate_claude_home** — Rite reads `~/.claude` and writes into the PROJECT. The one
  exception is the plugin's own status output. Installing, enabling or configuring anything
  under `~/.claude` requires explicit user consent through the `claude` CLI — never a silent write.
- **standard_vs_scheduling** — Rite owns the per-project contract: which files exist, their
  shape, their freshness. project-tracker owns cross-project scheduling: which project to
  touch tonight. Neither reaches into the other's question.
- **verify_against_the_machine** — After the first line of code exists, a doc claim is a
  testable assertion. Freshness is measured against source mtime, commit activity, or the host
  — NEVER against another document. Errors propagate doc-to-doc; that is the failure mode
  being designed against.

## Layers

- **base** — works for anyone, any OS, no Costin stack. Python + portable paths.
  Contains: the standard, the session protocol, generic checks.
- **enrichment** — auto-detected. Present → extra checks light up. Absent → they skip silently.
  Contains: project-tracker registry, memory mirror, remote probes, machine caveats.

## Data flow

**spec_render** — trigger: manual, or a pre-commit gate.
Reads `spec/project-standard.yaml`, writes `spec/PROJECT-STANDARD.md`.
Gate: `render-standard.py --check` exits 1 on drift.
The project applies its own principle to its own spec on day one.

**session_start** — BUILT, `scripts/rite_session_start.py`. Reads the project's `docs/*` and
`HANDOFF.md` front matter, and compares `written:` against the newest `LOG.md` entry. Writes one
thing: `hookSpecificOutput.additionalContext`, a verdict line. Never re-runs anything with side
effects; surfaces data AGE instead.

Two claims that stood here until 2026-09-09 were false and are corrected rather than quietly
edited away. It does **not** read an `/end` stamp file — `d-end-outcome-recorded-in-handoff`
rejected that file, and the outcome lives in `HANDOFF.md` front matter as
`session_end:`. It does **not** write `status.json`.

`status.json` is **dropped**, not pending — see `d-status-json-dropped-not-deferred`
(2026-09-09). It was to carry the SessionStart verdict as a file, and every candidate consumer
is unbuilt while the verdict itself already reaches the model live through the hook. An
artifact whose consumer does not exist is the mirror of a test that cannot run. The shape it
would have taken is preserved in that decision as a sketch, not a commitment; `mid_term`
`status-json-as-flag-accumulator` is the only route by which it returns.

The project side of it is the *measurement* against which `ROADMAP.current_state` is the
*claim*. Neither replaces the other — the value is in their disagreement, which turns "the
README says spec but `hooks/` exists" from something a human must notice into something that
fails. It is the one file in the project where a timestamp is mandatory rather than forbidden:
a generated document must be byte-stable so its drift gate works, but a measurement with no
measurement time is worthless.

## The three layers

Rite checks at three different rhythms, and only the third does not depend on someone
remembering:

| layer | when | depends on |
|---|---|---|
| **boundary** | session start and end | preflight fires by itself; `/end` fires only if the user types it |
| **document** | when the checker runs | someone running it |
| **continuous** | every write, every compaction | **nothing** — the harness fires it |

The continuous layer is the newest and the only mechanically reliable one. Hooks of
`type: command` are executed by the harness with no involvement from Claude and no action from
the user, which is exactly why they can police the halves that do depend on memory.

Two mechanics govern how a watcher reports, both verified 2026-09-08:

- **On tool events, plain-text stdout is discarded** — it reaches only the debug log, invisible
  to Claude and to the user. A watcher must emit JSON with `additionalContext`.
- **`additionalContext` reaches Claude; `systemMessage` reaches the user** — and on this machine
  `systemMessage` has no effect at all (0 references in 2.1.263). The channel that works is the
  one that talks to Claude, so watchers flag Claude and Claude tells the user.

## Rejected

- **Make the VS Code extension the product.** Eight incumbents already ship status-bar
  monitors. The differentiated half — session lifecycle and tool activity — is physically
  invisible to a plain extension, and a plugin reaches it.
- **Fork claude-preflight into a public copy.** Two copies drift. `checks.yaml` already makes
  the machine-specific checks toggles, so preflight can become a CONFIG of this engine with
  one codebase. Forking would recreate in code exactly the doc-rot this project exists to catch.
- **Keep the health-probe plugin from claude-persistent.** It emits `verdict` (a hardcoded
  constant), `source` (constant), `entrypoint` (redundant with `vscode.env.appName`) and
  `transcript_path`. Only the last has value, and the extension can derive it MORE correctly —
  workspace path → project slug → newest `.jsonl` — which also fixes the multi-window bug the
  single global status file has.
- **Absorb EVOLUTION.yaml into the standard.** It answers a scheduling question, not a
  project-contract question. Its schema (lanes, nodes, edges, branches, progress, slippages)
  is a timeline renderer. It belongs to project-tracker. See DECISIONS `d-evolution-out-of-scope`.
- **Hand-maintain PROJECT-STANDARD.md alongside the YAML.** The spec would become its own
  first doc-rot casualty. Generate it and gate the drift.
- **Timer-based reminders to the user** ("finish your session with /end"). Two independent
  reasons: a reminder that is always true carries no information and becomes wallpaper within a
  week — and `systemMessage`, the channel that would carry it, does nothing on this setup. The
  design argument and the harness agree. Watchers flag Claude; Claude tells the user.
- **`updatedInput` auto-fix** — silently rewriting a tool's input before it runs. It would make
  Claude reason from a version that is not on disk. In a project whose subject is documents
  that confidently describe something untrue, a mechanism that makes the agent confidently
  wrong about its own writes is the worst available feature. Block with exit 2 and say why.
- **A usage / time-to-reset gauge.** Not derivable on disk: `apiBlockIndex` is not a time window
  (measured — all four values span the same range), and `stats-cache.json` holds stale
  aggregates with no limit field. Rate-limit state is server-side. Any figure would be inferred
  while looking exact — the same failure as the hardcoded context-window map.
- **Aggregating transcripts across sessions to model usage.** Technically outside
  `d-profiling-never-integrated`, which names three specific files, but the same *shape*: a
  longitudinal behavioural dataset. If ever wanted it needs its own decision, never arrival as
  a side effect of a token counter.
- **Convert DECISIONS and ROADMAP to Markdown along with the rest.** Their tests read fields,
  not paragraphs. Heading-scraping would mean writing a bespoke structure parser to avoid a
  dependency that is already installed.

## Dependencies

- runtime: **Python 3 — stdlib only**, Claude Code with plugin support

  Python is Rite's **one declared prerequisite** — `/log`, `/mirror-memory`, the checker and
  the preflight port are all Python — and it is the *only* one. There is nothing to
  `pip install`: the YAML the project uses is read by a stdlib-only subset parser, so the
  install cost is Linux 0, macOS 0–1, Windows 1. Python's presence is surfaced at preflight,
  visibly, rather than assumed.

  Node is not an alternative: Claude Code ships a self-contained binary and does not put `node`
  on PATH. See `d-python-is-the-runtime`.
- optional: git (freshness signals), project-tracker (enrichment only)
- none of: Anthropic code, network calls, AI inference at check time

## Open architecture questions

- **plan_attribution** — Memory directories encode the project in their path; `~/.claude/plans`
  does not — names are harness gibberish (`cheeky-seeking-clock.md`). Recovering plan → project
  needs mtime/session correlation or content inspection. The only genuinely hard part of the
  mechanical half.
- **history_at_two_grains** — `LOG.md` and `ROADMAP.milestones` deliberately overlap in
  subject and differ in resolution. Nothing yet enforces that a milestone's `log_ref` points at
  a real LOG line, and the LOG format carries no item id — see `c-log-has-no-item-ids`.
- **log_ownership_overlap** — project-tracker's `ARCHITECTURE.yaml` already declares `LOG.md` a
  per-project artifact it creates. Resolved in DECISIONS `d-log-ownership-split`, but the
  tracker's own docs will need updating to match.
