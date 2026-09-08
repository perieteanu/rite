# `tools/` — archived copies of code written outside this repo

Same problem as the memory mirror and plan copy, a third time: an agent-authored artifact that
lives outside the project and would otherwise be lost.

`~/projects/claude-run/` is explicitly a **prunable** directory — its own README says "these
are hand-off / throwaway scripts — prune freely". So a script written there for this project
will eventually be deleted, and with it the record of how something was done. Copying it here
preserves it in the project that occasioned it.

**Write discipline: `write_once`.** These are archives, like `docs/PLAN-*.md`. The living copy
is the one in `claude-run` (or wherever it graduated to). Editing an archive falsifies a record
of what was actually run.

**Nothing here ships as part of the plugin.** `TOOL-2026-09-08-plugin-probe.sh` installs and
removes Claude Code plugins — it writes to `~/.claude`, which Rite itself must never do
(`never_mutate_claude_home`). A plugin that could install itself would violate its own
boundary. These are local operational scripts, archived, not distributed.

| file | what it was for |
|---|---|
| `TOOL-2026-09-08-plugin-probe.sh` | Install a plugin and diff what changed. Reversing an install is easy; noticing what it did is not. Live copy: `~/projects/claude-run/claude-plugin-probe-20260908.sh` |

**Open:** whether `tools/` becomes a declared artifact of the standard. The inventory is frozen
at 13 and a 14th requires a DECISIONS entry — so this directory currently exists as project
plumbing, not as part of the standard. Do not add it to the spec without that entry.
