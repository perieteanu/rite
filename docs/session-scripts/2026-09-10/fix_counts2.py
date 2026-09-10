import pathlib, sys
edits = [
 ("README.md",
  "test needs an installed plugin — so the runner reports **`9 of 11 gates ran`** and names the two",
  "test needs an installed plugin — so the runner reports **`10 of 12 gates ran`** and names the two"),
 ("docs/ARCHITECTURE.md",
  "no installed plugin) — so the runner prints `9 of 11 gates ran` and names what was not enforced.",
  "no installed plugin) — so the runner prints `10 of 12 gates ran` and names what was not enforced."),
 ("CLAUDE.md",
  "- **CI runs ELEVEN gates, but only nine of them on a runner.** `.github/workflows/gates.yml`",
  "- **CI runs TWELVE gates, but only ten of them on a runner.** `.github/workflows/gates.yml`"),
 ("CLAUDE.md",
  "- **The artifact inventory is FROZEN at 13** (2026-09-07). A 14th requires a DECISIONS entry.",
  "- **The artifact inventory is FROZEN at 14** (13 on 2026-09-07; `script_copy` added 2026-09-10\n"
  "  by `d-session-scripts-are-the-fourteenth-artifact`, which is the process working rather than\n"
  "  the freeze failing). A 15th requires a DECISIONS entry."),
 ("CLAUDE.md",
  "- **No port of `preflight.py` / `claude-mirror-memory.py` / `hookdedup.py`**, and no\n"
  "  `checks.yaml` — `port-preflight` has not started.",
  "- **No port of `preflight.py` or `hookdedup.py`**, and no `checks.yaml` — `port-preflight` has\n"
  "  not started. `claude-mirror-memory.py` IS ported, as `scripts/rite_copy.py`, alongside plan\n"
  "  and session-script copying; the global hook in `~/.claude/settings.json` is deliberately\n"
  "  still running beside it until the port is proven."),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}\n  {old[:70]}")
    b = len(t.encode("utf-8"))
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"{rel}: {b} -> {len(p.read_bytes())}")
