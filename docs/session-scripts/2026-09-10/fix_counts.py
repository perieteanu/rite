import pathlib, sys
ROOT = pathlib.Path("/home/perieteanu/projects/rite")
edits = [
    ("README.md",
     "test needs an installed plugin — so the runner reports **`7 of 9 gates ran`** and names the two",
     "test needs an installed plugin — so the runner reports **`9 of 11 gates ran`** and names the two"),
    ("docs/ARCHITECTURE.md",
     "no installed plugin) — so the runner prints `7 of 9 gates ran` and names what was not enforced.",
     "no installed plugin) — so the runner prints `9 of 11 gates ran` and names what was not enforced."),
    ("CLAUDE.md",
     "- **CI runs NINE gates, but only seven of them on a runner.** `.github/workflows/gates.yml`",
     "- **CI runs ELEVEN gates, but only nine of them on a runner.** `.github/workflows/gates.yml`"),
    ("docs/ROADMAP.yaml",
     "  NINE GATES RUN, AND CI NOW RUNS THEM: standard, protocol, riteyaml differential, hook output",
     "  ELEVEN GATES RUN, AND CI NOW RUNS THEM: standard, protocol, generated blocks, riteyaml\n"
     "  differential, stage-table guard, hook output"),
    ("docs/ROADMAP.yaml",
     "  but only SEVEN of the nine gates can run on a runner: the riteyaml differential needs PyYAML",
     "  but only NINE of the eleven gates can run on a runner: the riteyaml differential needs PyYAML"),
]
for rel, old, new in edits:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {text.count(old)} times\n  {old[:70]}")
    b = len(text.encode("utf-8"))
    p.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print(f"{rel}: {b} -> {len(p.read_bytes())}")
