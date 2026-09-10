import pathlib, sys
edits = [
 ("docs/ROADMAP.yaml",
  "  Rite is an installed, running plugin at version 0.12.0 — rite@rite, five skills reachable as\n"
  "  /rite:log /rite:preflight /rite:handoff /rite:end /rite:init, and a SessionStart hook whose verdict line\n",
  "  Rite is an installed, running plugin at version 0.15.0 — rite@rite, six skills reachable as\n"
  "  /rite:log /rite:preflight /rite:handoff /rite:end /rite:init /rite:update, and a SessionStart hook whose verdict line\n"),
 ("docs/ARCHITECTURE.md",
  "skills/              /rite:log /rite:end /rite:handoff /rite:preflight /rite:init\n",
  "skills/              /rite:log /rite:end /rite:handoff /rite:preflight /rite:init /rite:update\n"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"{rel} updated")
