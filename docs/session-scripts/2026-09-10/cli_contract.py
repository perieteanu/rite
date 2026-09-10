import pathlib, sys
p = pathlib.Path("scripts/rite-check.py")
t = p.read_text(encoding="utf-8")
old = '''def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    force = "--force" in argv
'''
new = '''USAGE = """rite-check — score a project against the Rite standard.

Usage:
  rite-check.py [PROJECT_DIR] [--force] [--exclude-scope=SCOPE]

  PROJECT_DIR             the project to check (default: the current directory)
  --force                 check a project that has no .rite.yaml marker, answering
                          "what would this score if it opted in?" It reads; it never writes.
  --exclude-scope=SCOPE   skip every test declaring that `scope:`, reporting each as NA
                          naming the exclusion. Note the `=`; the separate form is rejected,
                          because a bare value would be read as PROJECT_DIR.
  -h, --help              this message

Exit: 0 pass (or nothing to do) · 1 a RED finding · 2 a usage error
"""

# The flags this tool actually has. Anything else is a usage error rather than a silent no-op:
# until 2026-09-10 every unrecognised flag was discarded, so `--help` ran a full check and a
# typo'd `--exclude-scpoe=session` scored at FULL strength while the caller believed a scope had
# been excluded. A flag that looks accepted and does nothing is a silent wrong answer, which is
# the failure class this project exists to attack — here in its own entry point.
KNOWN_FLAGS = frozenset({"--force"})
KNOWN_FLAG_PREFIXES = ("--exclude-scope=",)
HELP_FLAGS = frozenset({"-h", "--help"})


def parse_flags(argv: list[str]) -> tuple[list[str], str | None]:
    """(unknown flags, help requested)."""
    unknown = []
    wants_help = False
    for a in argv:
        if not a.startswith("-") or a == "-":
            continue
        if a in HELP_FLAGS:
            wants_help = True
        elif a not in KNOWN_FLAGS and not a.startswith(KNOWN_FLAG_PREFIXES):
            unknown.append(a)
    return unknown, wants_help


def main(argv: list[str]) -> int:
    unknown, wants_help = parse_flags(argv[1:])
    if wants_help:
        print(USAGE, end="")
        return 0
    if unknown:
        plural = "s" if len(unknown) > 1 else ""
        print(f"rite-check: unknown option{plural}: {', '.join(unknown)}", file=sys.stderr)
        if any(a.startswith("--exclude-scope") for a in unknown):
            print("            did you mean --exclude-scope=SCOPE, with an '='?", file=sys.stderr)
        print("            run with --help for usage.", file=sys.stderr)
        return 2

    args = [a for a in argv[1:] if not a.startswith("-")]
    force = "--force" in argv
'''
if t.count(old) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("CLI contract added")
