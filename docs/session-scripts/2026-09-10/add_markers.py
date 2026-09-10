import pathlib, sys
ROOT = pathlib.Path("/home/perieteanu/projects/rite")

edits = [
    # the template target keeps its "you are here" pointer, declared as data
    ("spec/project-standard.yaml",
     "        - path: template/.rite.yaml\n          style: yaml_comment\n",
     "        - path: template/.rite.yaml\n"
     "          style: yaml_comment\n"
     "          # A scaffolded project is always at `idea`, so the pointer is a constant of the\n"
     "          # template rather than something the generator could infer. Declared, not lost.\n"
     "          annotations:\n"
     "            idea: \"<- you are here\"\n"),

    ("README.md",
     "| stage | what it adds |\n"
     "|---|---|\n"
     "| `idea` | `LOG.md`, `HANDOFF.md` |\n"
     "| `spec` | `README.md`, `CLAUDE.md`, `docs/MISSION.md`, `docs/ROADMAP.yaml` |\n"
     "| `build` | `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/DECISIONS.yaml` |\n"
     "| `shipped` | `LICENSE` |\n",
     "<!-- rite:generated stage-table -->\n"
     "| stage | what it adds |\n"
     "|---|---|\n"
     "| `idea` | `LOG.md`, `HANDOFF.md` |\n"
     "| `spec` | `README.md`, `CLAUDE.md`, `docs/MISSION.md`, `docs/ROADMAP.yaml` |\n"
     "| `build` | `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/DECISIONS.yaml` |\n"
     "| `shipped` | `LICENSE` |\n"
     "<!-- /rite:generated -->\n"),

    ("template/.rite.yaml",
     "#   idea      LOG.md, HANDOFF.md                          <- you are here\n"
     "#   spec      + README.md, CLAUDE.md, MISSION, ROADMAP\n"
     "#   build     + ARCHITECTURE, CONVENTIONS, DECISIONS\n"
     "#   shipped   + LICENSE\n",
     "# rite:generated stage-table\n"
     "#   idea      LOG.md, HANDOFF.md                          <- you are here\n"
     "#   spec      + README.md, CLAUDE.md, MISSION, ROADMAP\n"
     "#   build     + ARCHITECTURE, CONVENTIONS, DECISIONS\n"
     "#   shipped   + LICENSE\n"
     "# /rite:generated\n"),
]

for rel, old, new in edits:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {text.count(old)} times, expected 1")
    before = len(text.encode("utf-8"))
    p.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print(f"{rel}: {before} -> {len(p.read_bytes())} bytes")
