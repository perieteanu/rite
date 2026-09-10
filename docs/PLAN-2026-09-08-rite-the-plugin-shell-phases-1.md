<!-- Copied from ~/.claude/plans/tranquil-mapping-hinton.md on 2026-09-10.
     Plans are written outside the project under harness-generated names carrying no
     project attribution; they are lost when the session ends unless copied. Canonical
     name per spec/project-standard.yaml artifact `plan_copy`. Copied by rite_copy.py,
     which attributes a plan to the project whose SESSION wrote it. -->

# Rite — the plugin shell (phases 1 + 2)

## Context

Rite has two written specs, a YAML parser, a working checker that discriminates across five
real projects, and a git repo. **None of it runs unless invoked by hand.** That is the
project's own founding complaint one level up: a rule with no completion test is not a rule,
and a checker nobody runs automatically is exactly that.

There is still no `.claude-plugin/`, no `skills/`, no `hooks/` — Rite is not installable.
This plan makes it installable and makes the session protocol actually fire.

Scope agreed: **phases 1 and 2**. Phase 1 is the judgement half (zero prerequisites).
Phase 2 is the three core hooks (needs Python + shims). The eight watchers, LICENSE and
publication are explicitly out.

## What already exists (do not rebuild)

| path | role |
|---|---|
| `scripts/riteyaml.py` | stdlib YAML subset parser. Use for all YAML reads. |
| `scripts/rite-check.py` | the checker. `--force` evaluates a non-participating project. |
| `spec/session-protocol.yaml` | **the authority for what each skill must do.** 4 phases, 5 tests. |
| `spec/project-standard.yaml` | `verdicts`, `participation`, `capabilities`, `portability`. |
| `.rite.yaml` | the opt-in marker. |

## Layout decision — one unknown to settle first

Verified from the docs: a **single plugin** is `.claude-plugin/plugin.json` at its root plus
`skills/`, `hooks/`, `scripts/`. A **marketplace** is a different thing — `marketplace.json`
listing plugins by source path. The "locked finding" in `CLAUDE.md` conflates the two and
must be corrected.

Costin's proven local pattern (`claude-persistent/slice/marketplace/`) nests the plugin under
`plugins/<name>/`. Rite cannot copy that directly: `scripts/` already lives at the repo root
and `render-standard.py` resolves it as `HERE.parent / "scripts"`.

**Approach: make the repo root the plugin**, and have it advertise itself.

```
rite/
├── .claude-plugin/
│   ├── plugin.json          name, description, author{name: "Costin"}
│   └── marketplace.json     plugins: [{name: "rite", source: "."}]
├── skills/<name>/SKILL.md   phase 1
├── hooks/hooks.json + *.sh  phase 2
├── scripts/                 EXISTS — hooks call into it
└── spec/ docs/ …            unchanged
```

**FIRST TASK, blocking:** verify `"source": "."` is accepted by
`/plugin marketplace add ~/projects/rite`. If it is rejected, fall back to `plugins/rite/`
with `scripts/` moved and `render-standard.py`'s path updated. Do not build on the assumption.

## Phase 1 — the judgement half (no prerequisites)

Four skills as `skills/<name>/SKILL.md`. Docs state `commands/*.md` is the legacy form and
both load identically; skills are the current form and give `/rite:end`.

**Body style must match the five existing commands in `~/.claude/commands/`** — that is the
house style and Costin reads it fluently: opening prose stating what it does and its posture,
then `## Steps` as an imperative numbered list naming exact tools and paths, explicit
human-in-the-loop pauses ("**Wait for the user.** Do not append before approval"), and a
closing `## Don't` of 3–5 negatives. 40–140 lines. No emojis.

Frontmatter: `name`, `description`, `argument-hint` — plus `disable-model-invocation` where
noted. (The existing commands use only `description` + `argument-hint`; skills need `name`.)

| skill | invocation | must do |
|---|---|---|
| `skills/end/SKILL.md` | **`disable-model-invocation: true`** | The five steps of `phases.end_judgement`: distil the log · update what changed · close roadmap items (delete → append milestone) · **record `session_end:`** · write memory. Claude must never decide a session is over. |
| `skills/log/SKILL.md` | both (model + user) | Append one entry. **Read the clock per entry** — never extrapolate. This is the step that failed twice in two days. |
| `skills/handoff/SKILL.md` | **`disable-model-invocation: true`** | One of four outcomes; `genre: none` is a real answer. `expires` is always a date. |
| `skills/preflight/SKILL.md` | user-invocable | Run `rite-check.py`, report verdicts with whose-side-to-fix, plus the capability report. **Never instructs an installation** (`d-never-instruct-installation`). |

Each skill states the rule it enforces and **why**, because a prompt that only lists steps
gets skimmed. `/log` must carry the timestamp rule prominently.

## Phase 2 — the three core hooks

**Shims first.** `hooks/rite.sh` and `hooks/rite.ps1`, per
`portability.shell_only_as_a_launcher`: try `python3`, then `python`, then `py`; on success
exec the real work; on failure print what is missing and how it degrades, **never an install
command**, exit non-zero. Nothing else — no logic, no checks.

`hooks/hooks.json`, shape confirmed against health-probe and the docs:

```json
{ "hooks": { "SessionStart": [ { "hooks": [ { "type": "command",
  "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh\" session-start",
  "timeout": 15 } ] } ] } }
```

| event | matcher | script | does |
|---|---|---|---|
| `SessionStart` | `startup`, `resume` (separate entries, per Costin's settings) | `scripts/rite_session_start.py` | run the checker · compare `HANDOFF written:` to newest LOG entry · surface or fail on the handoff · emit **`additionalContext`** |
| `PostToolUse` | `Write\|Edit\|MultiEdit` | reuse `claude-mirror-memory.py --hook` | mirror memory. Do NOT re-implement; it works. |
| `SessionEnd` | none | `scripts/rite_session_end.py` | copy plans, final mirror. **Mechanical only** — no turns remain. |

**Output rule that decides the design:** on tool events, plain stdout goes to the debug log
only — invisible to both Claude and the user. Anything that must reach Claude is JSON with
`additionalContext`. `systemMessage` does nothing on this machine.

**The nag-once contradiction is unresolved** (`spec/session-protocol.yaml` → `honest_limits`):
recording that a report was delivered wants HANDOFF front matter, but HANDOFF is `write_once`
and freezes at session end. **Settle this before writing the SessionStart script.** Cheapest
option: nag is stateless and recomputed each start, reported once per session rather than once
ever — which is weaker than the ruling but violates nothing.

## Migration — how the old setup and Rite coexist

The machine already runs, from `~/.claude/settings.json`:

- `SessionStart` (matchers `startup` and `resume`) → `preflight.py --hook` **and**
  `claude-mirror-memory.py --check`
- `PostToolUse` on `Write|Edit|MultiEdit` → `claude-mirror-memory.py --hook`
- `~/.claude/commands/`: `log`, `next`, `preflight`, `mirror-memory`, `global-audit`
- plugin `health-probe@persistent-dev` enabled

**Rite must not switch this over, and cannot.** `never_mutate_claude_home` forbids Rite
writing to `~/.claude` — installing, enabling or reconfiguring anything there is the user's
action through the `claude` CLI. So the deliverable is a printed diff, never an applied one.

**These phases COEXIST rather than replace.** The split that makes that safe already exists:
preflight tags findings `claude` / `project` / `machine`, and `rite-check.py` emits **only
`project`** findings. So Rite covers the project side; preflight keeps machine and claude.

- **Known overlap, accepted:** preflight's `last_log_age` and `mirror_drift` are project-side
  and will double up with Rite's `newest_entry_within_days_of_activity`. Two YELLOW lines
  about the same log. Noisy, not wrong. Note it; do not fix it here.
- **Do NOT re-implement the memory mirror.** Phase 2's PostToolUse hook calls the existing
  `claude-mirror-memory.py --hook`. It works, and a second implementation is the drift
  `d-preflight-is-config-not-fork` refuses.
- **The real switchover belongs to `port-preflight`**, which is out of scope. That is when
  `preflight.py` becomes a `checks.yaml` of the Rite engine and the old SessionStart entries
  come out of `settings.json`.

**Name collision is an unverified risk and must be tested, not assumed.** The docs say both
"when a skill and command share the same name, the skill takes precedence" *and* "the bare
`/fancy` also works unless another command uses that name" — those are in tension. Rite ships
skills named `log`, `preflight` and `handoff`; Costin has commands named `log` and `preflight`.
**Test immediately after install: does bare `/log` still run `~/.claude/commands/log.md`?**
If Rite shadows it silently, that is a behaviour change he did not ask for — rename Rite's
skills (`rite-log`) rather than let it shadow.

**Rollback must exist before install:** copy `~/.claude/settings.json` to a timestamped
backup, and record that `/plugin` disable is the off switch. Under
`entrypoint=claude-vscode` the `/plugin` TUI is unavailable — install and removal go through
the `claude` shell CLI.

## Docs that must change in the same pass

`ARCHITECTURE.md` "Planned, not built" (three of five entries land) · `CLAUDE.md`
"Explicitly NOT built yet" and the marketplace-vs-plugin locked finding · `ROADMAP`
`current_state`, and close `plugin-packaging` into a milestone · new ADR for the layout
decision.

`must_be_current` claims went false twice today the moment code landed. Expect it again.

## Verification

0. **Back up `~/.claude/settings.json`** to a timestamped copy before installing anything.
1. `python3 scripts/rite-check.py` → 0 RED, and `--check` on both specs → OK.
2. `/plugin marketplace add ~/projects/rite` then install; confirm `/rite:end` etc. appear.
2b. **Collision test, immediately:** does bare `/log` still run `~/.claude/commands/log.md`?
    Does `/preflight` still run the old one? If either is shadowed, rename Rite's skills.
2c. **Duplication test:** start a session and count verdict lines. Expect one from preflight
    and one from Rite covering different sides — not two of the same.
3. **Phase 1 with no Python on PATH** — the four skills must still work. That is the claim
   `capabilities.degradation_tiers` makes; test it rather than assert it.
4. Shim failure path: run it with `python3`/`python`/`py` all absent; it must name what is
   missing and exit non-zero **without printing an install command**.
5. SessionStart: start a real session and confirm the verdict reaches the transcript via
   `additionalContext`.
6. Handoff detection: set `written:` older than the newest LOG entry; SessionStart must report
   the session did not close. Restore afterwards.
7. `git status` clean; commit per phase, no `Co-Authored-By` trailer.

## Out of scope

The eight watchers (two depend on unverified mechanics) · `port-preflight` · LICENSE ·
`claim-namespaces` · GitHub remote and publication · the three unimplemented checker rules.
