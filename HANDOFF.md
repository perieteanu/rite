---
genre: task_brief
written: "2026-09-08"
session_end: written
supersedes: "the 2026-09-08 14:00 handoff"
expires: "2026-12-07"
status: live
---

# HANDOFF — rite

**You were started to test one thing the previous session could not: what the installed plugin
actually does inside a live session.** Do that first, before anything else.

## The test, in order

Rite is **installed and enabled** (`rite@rite`, user scope). Two of its skills share names with
Costin's own commands, and the docs contradict themselves about which wins.

1. Type `/` and list what appears. Report the exact names — `end`, `log`, `preflight`,
   `handoff`, and whether they show bare or as `rite:end` etc.
2. **The one that matters:** run `/log` and observe which one runs.
   - **Costin's** (`~/.claude/commands/log.md`) also matches `[done] X` against
     `next-steps.yaml` and proposes removing the completed step.
   - **Rite's** (`skills/log/SKILL.md`) deliberately never touches that file
     (`d-project-tracker-stays-separate`) and instead insists the clock is read per entry.
   - If Rite shadows his, he silently loses a daily integration. **Report it; do not fix it.**
3. Same for `/preflight` — his runs `claude-preflight`; Rite's runs `rite-check.py`.
4. Confirm the SessionStart hook fired: this session's context should carry a
   `rite — project standard: 54 checks · 0 RED …` line, in addition to the usual preflight
   verdict. Two lines covering different sides is correct; two saying the same thing is not.

**Reverse if anything is wrong:**
`~/projects/claude-run/claude-plugin-probe-20260908.sh --off rite`

## State (verified 2026-09-08 19:01)

| | |
|---|---|
| plugin | installed, enabled, `rite@rite`, 4 skills + 2 hooks |
| checker | `scripts/rite-check.py`, 49/57 rules, 0 RED on rite |
| parser | `scripts/riteyaml.py`, stdlib only, no PyYAML anywhere |
| gates | standard OK · protocol OK · riteyaml PASS |
| ADRs / LOG / commits | 33 · 189 · 8 |
| still missing | LICENSE, `PostToolUse`, the 8 watchers, publication |

## Settled today — do not re-litigate

`d-plugin-layout-root-is-the-plugin` (root IS the plugin; skills not commands; nag state in
`${CLAUDE_PLUGIN_DATA}`) · `d-verdicts-and-participation` · `d-git-is-a-capability-not-a-prerequisite`
· `d-never-instruct-installation` · `d-drop-claims-match-stage` · `d-stdlib-only-yaml-subset`.

Absolute, unchanged: **never touch `ai-collab-profile/`, `prompts.db`, `prompts-corpus.jsonl`.**

## Traps

- **Read the machine clock per LOG entry.** Extrapolating produced ~30 fabricated timestamps on
  07-09 and a second batch on 08-09, the latter with `date` output visible in the same command.
- Both `spec/*.md` are generated; edit the `.yaml` and regenerate. Two gates.
- `docs/` is deliberately mixed — prose is Markdown, structure is YAML, per file.
- Closing a roadmap item means **deleting** it and **appending** a milestone.
- `ROADMAP` is three zones; the integrity checks compare the **zone**, not the file.
- Rite must never write to `~/.claude`. The probe script does, which is exactly why it lives
  in `claude-run` and not in this repo.

## Known, unresolved

- **`claude plugin install` silently dropped `effortLevel: "max"`** from `settings.json` on
  08-09. Restored. If it recurs after any plugin operation, that is the CLI, not Rite.
- **The whole repo ships to the install cache** — 604K including this project's LOG.md and
  `tools/`. Root-as-plugin bought a working checker at that price. No exclusion mechanism found.
- **~225 tokens always-on, every session**, for four skills. Measured via
  `claude plugin details rite`. An argument for fewer skills, not yet acted on.
- `c-unimplementable-tests` is down to **one**: `claims_match_filesystem`, which needs the
  machine-readable claim surface Costin deferred.
- Whether `tools/` becomes a declared artifact needs a DECISIONS entry. Inventory frozen at 13.

## Next, after the test

`LICENSE` (rite fails its own standard at stage `shipped` without one) · the three
unimplemented checker rules · `port-mirror-memory`, which is where `PostToolUse` belongs ·
then the watchers.
