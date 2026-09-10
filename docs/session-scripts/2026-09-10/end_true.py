import pathlib, sys
edits = [
("docs/ROADMAP.yaml",
 "  Rite is an installed, running plugin at version 0.20.0 — rite@rite, six skills reachable as\n"
 "  /rite:log /rite:preflight /rite:handoff /rite:end /rite:init /rite:update, and a SessionStart hook whose verdict line\n",
 "  Rite is an installed, running plugin at version 0.22.0 — rite@rite, SEVEN skills reachable as\n"
 "  /rite:log /rite:preflight /rite:handoff /rite:end /rite:init /rite:update /rite:issue, and a SessionStart hook whose verdict line\n"),
("docs/ARCHITECTURE.md",
 "                     tests. 63 checks on this project; 62 of 63 declared tests implemented.",
 "                     tests. 64 checks on this project; 64 of 64 declared tests implemented."),
("CLAUDE.md",
 "- **ONE of the eight watchers.** `watcher-write-discipline` is built — `scripts/rite_watch.py`,\n"
 "  PostToolUse, reporting an append-only file rewritten or a LOG entry dated in the future, and\n"
 "  silent otherwise. The other seven are unbuilt, and **two have lost their premise**:\n"
 "  `watcher-plan-copy-on-create` bought attribution that transcript-reading now does exactly,\n"
 "  and `watcher-precompact-distiller` still rests on an unverified claim about `PreCompact`.\n",
 "- **TWO of the eight watchers**, both in `scripts/rite_watch.py`, which dispatches on the event.\n"
 "  `watcher-write-discipline` (PostToolUse) reports an append-only file rewritten or a LOG entry\n"
 "  dated in the future. `watcher-cwd-changed` reports a mid-session move to a DIFFERENT marked\n"
 "  project, once — because Rite assumes one project per session and every artifact resolves from\n"
 "  one root. Both are silent otherwise, which is a contract and not politeness.\n"
 "  The other six are unbuilt, and **two have lost their premise**: `watcher-plan-copy-on-create`\n"
 "  bought attribution that transcript-reading now does exactly, and `watcher-precompact-distiller`\n"
 "  still rests on an unverified claim about `PreCompact`.\n"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"  ok  {rel}")

# current_state: today's last stretch
r = pathlib.Path("docs/ROADMAP.yaml")
t = r.read_text(encoding="utf-8")
anchor = "  STILL MISSING: ONE declared rule is unimplemented, deleted_ids_appear_in_milestones."
new_state = '''  THE CHECKER IS AT FULL COVERAGE — 64 of 64 declared tests implemented, 0 NA on this project,
  for the first time. deleted_ids_appear_in_milestones was the last, and it is what makes the
  deletion convention safe: closing an item by deleting it is only sound if the item is promoted
  rather than erased. required_any_of_sections was implemented all along and invoked by NOTHING,
  because the spec declared its data under `structure:` while no artifact listed the rule under
  `tests:`; wiring it exposed that it also ignored the section_aliases declared beside it.
  TWO WATCHERS RUN, both in scripts/rite_watch.py dispatching on the event: write discipline on
  PostToolUse, and a once-per-session notice when the cwd moves to a different marked project.
  /rite:issue records what RITE got wrong from whatever project you hit it in, appending to
  ${CLAUDE_PLUGIN_DATA}/feedback.md and never to the project you are in.
  THE FIRST REAL `command:` CHECK IS LIVE and it is not in this repo: tracker_registered reads
  project-tracker's projects.yaml from ~/.claude/scripts, wired in Costin's own checks.yaml.
  That is the mechanism working as designed — the engine never learns that file's shape.
  STILL MISSING: no declared rule is unimplemented.'''
if t.count(anchor) != 1:
    sys.exit("ABORT current_state")
r.write_text(t.replace(anchor, new_state, 1), encoding="utf-8", newline="\n")
print("  ok  current_state")
