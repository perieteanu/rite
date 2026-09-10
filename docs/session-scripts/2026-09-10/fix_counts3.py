import pathlib, sys
edits = [
 ("README.md",
  "test needs an installed plugin — so the runner reports **`10 of 12 gates ran`** and names the two",
  "test needs an installed plugin — so the runner reports **`10 of 13 gates ran`** and names the three"),
 ("docs/ARCHITECTURE.md",
  "no installed plugin) — so the runner prints `10 of 12 gates ran` and names what was not enforced.",
  "no installed plugin) — so the runner prints `10 of 13 gates ran` and names what was not enforced."),
 ("CLAUDE.md",
  "- **CI runs TWELVE gates, but only ten of them on a runner.** `.github/workflows/gates.yml`",
  "- **CI runs THIRTEEN gates, but only ten of them on a runner.** `.github/workflows/gates.yml`"),
 ("docs/ROADMAP.yaml",
  "  ELEVEN GATES RUN, AND CI NOW RUNS THEM: standard, protocol, generated blocks, riteyaml\n  differential, stage-table guard, hook output",
  "  THIRTEEN GATES RUN, AND CI NOW RUNS THEM: standard, protocol, generated blocks, riteyaml\n  differential, mirror-port parity, stage-table guard, copy attribution, hook output"),
 ("docs/ROADMAP.yaml",
  "  but only NINE of the eleven gates can run on a runner: the riteyaml differential needs PyYAML",
  "  but only TEN of the thirteen gates can run on a runner: the riteyaml differential needs PyYAML"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}\n  {old[:80]}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"{rel} updated")
