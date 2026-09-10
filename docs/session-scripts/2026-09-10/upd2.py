import pathlib, sys
edits = [
("docs/ROADMAP.yaml",
 "  Rite is an installed, running plugin at version 0.16.0 — rite@rite, six skills reachable as\n",
 "  Rite is an installed, running plugin at version 0.20.0 — rite@rite, six skills reachable as\n"),
("docs/ROADMAP.yaml",
 "  checker's coverage line now reads 61 of 62: `optional` markers were being counted in the\n"
 "  denominator as rules awaiting implementation, which understated the checker by four and had\n"
 "  four documents repeating 'seven declared tests unimplemented' for days. None of the eight\n"
 "  watchers; the PostToolUse hook exists but does one job, refreshing the memory mirror.\n",
 "  checker's coverage line now reads 62 of 63: `optional` markers were being counted in the\n"
 "  denominator as rules awaiting implementation, which understated the checker by four and had\n"
 "  four documents repeating 'seven declared tests unimplemented' for days.\n"
 "  THE FIRST WATCHER EXISTS — one of eight. scripts/rite_watch.py reports an append-only file\n"
 "  rewritten and a LOG entry dated in the future, on PostToolUse, silent otherwise. It closes\n"
 "  the gap honest_limits named: every implemented completion test was an end-of-session test.\n"
 "  It absorbed c-log-timestamps-must-be-machine-read, and scripts/riterules.py was extracted so\n"
 "  the watcher and the checker share one predicate rather than two free to disagree.\n"
 "  no_future_timestamps carries `scope: local_clock` and CI excludes it: LOG timestamps have no\n"
 "  timezone, so the question is only answerable on the machine that wrote them. CI proved that\n"
 "  on the first push by flagging 67 honest entries on three UTC runners.\n"),
("docs/ARCHITECTURE.md",
 "                     tests. 62 checks on this project; 61 of 62 declared tests implemented.",
 "                     tests. 63 checks on this project; 62 of 63 declared tests implemented."),
("CLAUDE.md",
 "- **None of the eight watchers.** The `PostToolUse` hook itself now exists — added 2026-09-10\n"
 "  with the copier port — but it does one job, refreshing the memory mirror when a memory file\n"
 "  is written. `watcher-write-discipline` and the other seven are unbuilt.\n",
 "- **ONE of the eight watchers.** `watcher-write-discipline` is built — `scripts/rite_watch.py`,\n"
 "  PostToolUse, reporting an append-only file rewritten or a LOG entry dated in the future, and\n"
 "  silent otherwise. The other seven are unbuilt, and **two have lost their premise**:\n"
 "  `watcher-plan-copy-on-create` bought attribution that transcript-reading now does exactly,\n"
 "  and `watcher-precompact-distiller` still rests on an unverified claim about `PreCompact`.\n"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"  ok  {rel}")
