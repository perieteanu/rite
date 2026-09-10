import pathlib, sys
edits = [
("docs/ARCHITECTURE.md",
 """hook ──► sh -c        (Linux, macOS)          ──┐
    ──► Git Bash     (Windows, recommended)   ──┤► shim ──► python3/python/py ──► Python
    ──► PowerShell   (Windows, no Git Bash)   ──┘   │
                                                   └─ not found ──► "Python 3 required: …", exit 1
""",
 """hook ──► sh -c        (Linux, macOS)          ──┐
    ──► Git Bash     (Windows, REQUIRED)      ──┴► rite.sh ──► python3/python/py ──► Python
                                                     │
                                                     └─ not found ──► "Python 3 required: …", exit 1

    ──► Windows without Git Bash              ──► HOOKS DO NOT RUN
""" ),
("docs/ARCHITECTURE.md",
 "Everything Rite does is Python, written once. The single exception is a launcher shim, whose\nonly job is to find an interpreter or explain that it cannot.\n",
 "Everything Rite does is Python, written once. The single exception is a launcher shim, whose\n"
 "only job is to find an interpreter or explain that it cannot.\n\n"
 "**`hooks.json` declares `shell: bash` on every entry, and Git Bash is therefore required on\n"
 "Windows.** Without it the harness falls back to PowerShell, which cannot run our command\n"
 "string — and a hook entry supports no per-platform conditional, so one string must serve every\n"
 "platform and no string does. `hooks/rite.ps1` remains as a MANUAL entry point; nothing invokes\n"
 "it automatically, and until 2026-09-10 the diagram below claimed otherwise. See\n"
 "`d-git-bash-required-on-windows`.\n"),
("README.md",
 "- **The freshness windows are guesses**",
 "- **Windows needs Git for Windows.** The hooks declare `shell: bash`, and without Git Bash the\n"
 "  harness has no shell that can run them — a hook entry supports no per-platform conditional,\n"
 "  so one command string must serve every platform and none does. Linux and macOS need nothing\n"
 "  beyond Python 3.\n"
 "- **The freshness windows are guesses**"),
("CLAUDE.md",
 "- `SessionEnd` exists as a hook event (verified in the 2.1.263 binary alongside `Stop`,",
 "- **A hook entry has NO per-platform conditional** — verified against the hooks reference\n"
 "  2026-09-10. Shell form sends the command to `sh -c` on Unix, Git Bash on Windows, or\n"
 "  PowerShell when Git Bash is absent; exec form (`args`) skips the shell but needs one\n"
 "  executable name that resolves everywhere, which is the problem the shim exists for. Entries\n"
 "  also accept `if`, `async`, `once` and `shell`. **Git Bash is required on Windows** —\n"
 "  `d-git-bash-required-on-windows`.\n"
 "- `SessionEnd` exists as a hook event (verified in the 2.1.263 binary alongside `Stop`,"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}\n  {old[:70]}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"{rel} updated")
