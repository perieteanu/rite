import pathlib, sys
ROOT = pathlib.Path("/home/perieteanu/projects/rite")

edits = [
    ("skills/preflight/SKILL.md",
     '   ```bash\n'
     '   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/rite-check.py" [PATH] [--force]\n'
     '   ```\n'
     '\n'
     '   Resolve `PATH` from `$ARGUMENTS`; default to the current project.\n',
     '   ```bash\n'
     '   bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" check [PATH] [--force]\n'
     '   ```\n'
     '\n'
     '   On Windows without Git Bash the same call is\n'
     '   `pwsh "${CLAUDE_PLUGIN_ROOT}/hooks/rite.ps1" check [PATH] [--force]`. Go through the\n'
     '   shim either way rather than calling the interpreter: it is the one place that knows\n'
     '   whether this machine has `py`, `python3` or `python`, and naming one of them here is\n'
     '   the rule `python_invocation_differs` — which this line broke until 2026-09-10.\n'
     '\n'
     '   Resolve `PATH` from `$ARGUMENTS`; default to the current project.\n'),

    ("skills/end/SKILL.md",
     '6. Run the checks before declaring the session closed. At minimum\n'
     '   `python3 scripts/rite-check.py`, plus whatever gates the project declares. Report the\n'
     '   result; do not claim done without it.\n',
     '6. Run the checks before declaring the session closed. At minimum\n'
     '   `bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" check` — or `rite.ps1` on Windows without\n'
     '   Git Bash — plus whatever gates the project declares. Report the result; do not claim\n'
     '   done without it.\n'),
]

for rel, old, new in edits:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {text.count(old)} times, expected 1")
    before = len(text.encode("utf-8"))
    p.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    after = len(p.read_bytes())
    print(f"{rel}: {before} -> {after} bytes (+{after-before})")
