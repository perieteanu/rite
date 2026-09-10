import pathlib, re, sys
p = pathlib.Path("scripts/rite_preflight.py")
t = p.read_text(encoding="utf-8")

def sub(old, new, label, count=1):
    global t
    if t.count(old) != count:
        sys.exit(f"ABORT {label}: matched {t.count(old)}, expected {count}")
    t = t.replace(old, new)
    print(f"  ok  {label}")

# 1 — config loader: riteyaml, not PyYAML
sub('''        try:
            import yaml
            data = yaml.safe_load(CONFIG_PATH.read_text()) or {}
        except Exception:
            data = {}''',
    '''        try:
            data = riteyaml.load(CONFIG_PATH.read_text(encoding="utf-8"),
                                 str(CONFIG_PATH)) or {}
        except Exception:
            # A malformed config must not stop the session POST. The defaults still run and
            # the report says which checks used them.
            data = {}''',
    "config loader")

# 2 — defaults gain the new keys
sub('''    "checks": {},
    "caveats": [],
    "remotes": [],
}''',
    '''    "checks": {},
    "caveats": [],
    "remotes": [],
    "project_markers": list(DEFAULT_PROJECT_MARKERS),
}''',
    "defaults")

# 3 — encoding on every read
EMPTY = chr(34) * 2
sub("def _read(path):\n    try:\n        return path.read_text()\n    except Exception:\n        return " + EMPTY,
    "def _read(path):\n    try:\n        return path.read_text(encoding=\"utf-8\", errors=\"replace\")\n    except OSError:\n        return " + EMPTY,
    "_read encoding")

# 4 — subprocess calls name encoding AND errors (the AST gate enforces this)
sub('''                out = subprocess.check_output(
                    ["claude", "mcp", "list"], stderr=subprocess.DEVNULL, timeout=20
                ).decode()''',
    '''                out = subprocess.run(
                    ["claude", "mcp", "list"], capture_output=True, text=True, timeout=20,
                    encoding="utf-8", errors="replace").stdout''',
    "mcp subprocess")

sub('''    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, timeout=10)''',
    '''    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, timeout=10,
                          encoding="utf-8", errors="replace")''',
    "git subprocess")

sub('''        out = subprocess.check_output(["df", "-P", *mounts],
                                      stderr=subprocess.DEVNULL, timeout=10).decode()''',
    '''        out = subprocess.run(["df", "-P", *mounts], capture_output=True, text=True,
                             timeout=10, encoding="utf-8", errors="replace").stdout''',
    "df subprocess")

# 5 — is_project_shaped no longer comes from AUDIT
sub("    proj_shaped = AUDIT and AUDIT.is_project_shaped(ctx.cwd)",
    "    proj_shaped = is_project_shaped(ctx.cwd, ctx.cfg)",
    "project_shaped call")

# 6 — /proc is Linux-only; a check that cannot run reports NA rather than raising
sub('''def _all_procs():
    """Snapshot {pid: (ppid, comm, cmdline)} for every process on the machine."""
    procs = {}''',
    '''PROC = Path("/proc")


def _all_procs():
    """Snapshot {pid: (ppid, comm, cmdline)} for every process on the machine.

    Linux only. macOS and Windows have no /proc, and the caller reports NA there rather than
    raising — a check that cannot run must never look like a check that passed.
    """
    procs = {}
    if not PROC.is_dir():
        return procs''',
    "/proc guard")

sub('''    procs = _all_procs()
    children = {}''',
    '''    procs = _all_procs()
    if not procs:
        return Result("parallel_claude", "claude", "NA",
                      "no /proc on this platform — cannot enumerate sessions", "")
    children = {}''',
    "parallel_claude NA")

p.write_text(t, encoding="utf-8", newline="\n")
print(f"rite_preflight.py: {len(p.read_bytes())} bytes")
