import pathlib, sys
edits = [
("docs/ARCHITECTURE.md",
 """**`PostToolUse` is deliberately absent.** The obvious implementation calls
`~/.claude/scripts/claude-mirror-memory.py`, which is Costin's script, not Rite's — a plugin
hook depending on a file only one machine has is broken by design for everyone else, and on
this machine it would double-fire against the entry already in `settings.json`. It lands with
`port-mirror-memory`.
""",
 """**`PostToolUse` exists as of 2026-09-10**, and the objection that kept it absent is gone
rather than overruled. It was absent because the obvious implementation called
`~/.claude/scripts/claude-mirror-memory.py` — Costin's script, not Rite's, so a plugin hook
depending on a file only one machine has, which would also double-fire against the entry in
`settings.json`. Both halves are now false: `scripts/rite_copy.py` is the port, and the
`settings.json` entry was retired in the same commit that added this hook.

It refreshes the memory mirror and **nothing else**, gated on the written path being a memory
file. A full refresh costs ~66ms and `PostToolUse` fires on every `Write` and `Edit`; paying
that on every edit to catch the few that touch a memory would be a tax on the whole session,
and a hook that makes editing feel slow is a hook the user removes.

It exists because `SessionEnd` copying could not cover the mid-session case. The mirror is read
from the workspace *while work happens*, so a mirror that is only correct after the session
ends is wrong for exactly as long as anyone would want to read it.
"""),
("docs/ARCHITECTURE.md",
 "hooks/            PostToolUse — belongs to port-mirror-memory (see below)\n",
 "hooks/            SubagentStop, PreCompact, FileChanged — the unbuilt watcher layer\n"),
("CLAUDE.md",
 "- **No `PostToolUse` hook**, and none of the eight watchers. It belongs to `port-mirror-memory`.\n",
 "- **None of the eight watchers.** The `PostToolUse` hook itself now exists — added 2026-09-10\n"
 "  with the copier port — but it does one job, refreshing the memory mirror when a memory file\n"
 "  is written. `watcher-write-discipline` and the other seven are unbuilt.\n"),
("docs/ROADMAP.yaml",
 "  source_plans_all_copied. No PostToolUse and none of the eight watchers.\n",
 "  source_plans_all_copied. None of the eight watchers — the PostToolUse hook exists but does\n"
 "  one job, refreshing the memory mirror.\n"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}\n  {old[:70]}")
    b = len(t.encode("utf-8"))
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"{rel}: {b} -> {len(p.read_bytes())}")
