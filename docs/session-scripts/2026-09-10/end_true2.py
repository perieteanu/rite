import pathlib, sys

a = pathlib.Path("docs/ARCHITECTURE.md")
t = a.read_text(encoding="utf-8")
old = """  rite_watch.py      THE WATCHER. PostToolUse: an append-only file rewritten, or a LOG entry
                     dated in the future. Silent on success — it fires on every write, and a
                     watcher that speaks when nothing is wrong gets disabled.
"""
new = """  rite_watch.py      THE WATCHER, dispatching on the event. PostToolUse: an append-only file
                     rewritten, or a LOG entry dated in the future. CwdChanged: a mid-session
                     move to a DIFFERENT marked project, once. Silent on success — it fires on
                     every write and every cd, and a watcher that speaks when nothing is wrong
                     gets disabled.
  rite_issue.py      Records what RITE got wrong, from any project, into plugin storage rather
                     than into the project you are in. Append-only and untriaged on purpose.
"""
if t.count(old) != 1:
    sys.exit("ABORT arch")
t = t.replace(old, new, 1)
t = t.replace("skills/              /rite:log /rite:end /rite:handoff /rite:preflight /rite:init /rite:update\n",
              "skills/              /rite:log /rite:end /rite:handoff /rite:preflight /rite:init /rite:update\n"
              "                     /rite:issue\n", 1)
a.write_text(t, encoding="utf-8", newline="\n")
print("  ok  ARCHITECTURE")

r = pathlib.Path("docs/ROADMAP.yaml")
t = r.read_text(encoding="utf-8")
old_c = "    - scripts/rite_watch.py\n"
new_c = "    - scripts/rite_watch.py\n    - scripts/rite_issue.py\n    - skills/issue/SKILL.md\n"
if t.count(old_c) != 1:
    sys.exit("ABORT claims")
r.write_text(t.replace(old_c, new_c, 1), encoding="utf-8", newline="\n")
print("  ok  claim surface")
