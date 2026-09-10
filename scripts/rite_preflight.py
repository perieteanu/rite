#!/usr/bin/env python3
"""rite_preflight — the session POST (power-on self-test): what is wrong, and whose side it is on.

A PORT of ~/projects/claude-preflight/preflight.py, not a fork —
d-preflight-is-config-not-fork, settled 2026-09-07: "Rite is the upstream engine. Costin's
preflight shrinks to his own checks.yaml plus checks too personal to publish." Check bodies are
carried over verbatim wherever behaviour is unchanged, because 748 lines proven over months are
worth more than a tidier reimplementation.

WHAT CHANGED IN THE PORT, and each has a reason rather than a preference:
  * Config is read with riteyaml, not PyYAML. Rite is stdlib-only. Verified before starting:
    riteyaml parses the real checks.yaml identically to PyYAML, with PyYAML as the oracle.
  * Config lives in ${CLAUDE_PLUGIN_DATA}/checks.yaml — plugin storage, which
    ARCHITECTURE's never_mutate_claude_home names as its one declared exception. It is NOT a
    project artifact, so the inventory stays at 14.
  * `is_project_shaped` no longer loads claude-global-audit.py, a script only one machine has.
    The markers are a config list, which is what they always were.
  * The global memory index path no longer hardcodes a username; the slug is derived.
  * Every read names encoding, and every subprocess names encoding AND errors — the AST gate
    enforces both, and the original predates that rule.
  * /proc and df are guarded. Both are absent on Windows and /proc on macOS, and a check that
    cannot run reports NA rather than raising.

WHAT IS DELIBERATELY NOT PORTED:
  * mirror_drift    — superseded by Rite's mirror_not_stale, which reads the sync stamp through
                      a predicate shared with the copier. The original compares mtimes, which
                      this project calls mtime theatre by name.
  * last_log_age    — superseded by newest_entry_within_days_of_activity.
  * tracker_registered — reads project-tracker's projects.yaml, which
                      d-project-tracker-stays-separate forbids the engine from knowing about.
                      It survives as a `command:` check in the user's own config.
  Restoring any of the three is a regression, not an omission.

Fast, deterministic session checkup. Surfaces *what's wrong and whose side it's on*
(claude/harness vs project vs machine), token-tight.

Invocation modes (see CLAUDE.md / README.md):
  preflight.py --hook    Called by the SessionStart hook. Runs the LOCAL tier, writes
                         the full report to last-post.txt, and emits ONLY a verdict to
                         context via hookSpecificOutput.additionalContext (JSON, exit 0):
                           GREEN  -> one terse line
                           YELLOW/RED -> verdict + only the failing checks + report path
                         Always exits 0 (never blocks session start).
                         Deduplicated: the VS Code extension dispatches one
                         SessionStart twice (~47ms apart), so a repeat of the
                         same session_id+source is suppressed (see already_emitted;
                         window: checks.yaml thresholds.hook_dedup_window_s).
  preflight.py           Manual run. LOCAL tier, human report to stdout.
  preflight.py --full    Manual run. LOCAL + NETWORK tiers, human report to stdout.

Reuses helpers from ~/.claude/scripts/claude-global-audit.py (locked decision #4):
days_since, registered_roots, configured_mcps, is_project_shaped. Loaded via importlib
because that filename contains dashes.
"""

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import riteyaml  # noqa: E402
import rite_copy  # noqa: E402
import ritededup  # noqa: E402

ritefs.use_utf8_stdio()

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"

# WRITES GO TO PLUGIN STORAGE, NEVER INTO ~/.claude ITSELF. ARCHITECTURE's
# never_mutate_claude_home names ${CLAUDE_PLUGIN_DATA} as its one declared exception, and the
# nag-once mechanism already lives there. Falling back to ~/.claude/rite keeps a bare run
# working when the harness has not set the variable.
DATA_DIR = Path(os.environ.get("CLAUDE_PLUGIN_DATA") or (CLAUDE_DIR / "rite"))
CONFIG_PATH = DATA_DIR / "checks.yaml"
REPORT_PATH = DATA_DIR / "last-post.txt"
STAMP_PATH = DATA_DIR / ".last-hook-stamp.json"

GLOBAL_CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"
SETTINGS_JSON = CLAUDE_DIR / "settings.json"
# The home-root slug is the GLOBAL memory. Derived, never spelled out: the original hardcoded
# "-home-perieteanu", which is one of the three machine-specific literals in 748 lines.
GLOBAL_MEMORY_INDEX = (CLAUDE_DIR / "projects" / rite_copy.encode_slug(HOME)
                       / "memory" / "MEMORY.md")

# `is_project_shaped` was a one-line helper in a script only this machine has. It is a list of
# marker filenames and always was, so it is config.
DEFAULT_PROJECT_MARKERS = ["CLAUDE.md", ".git", "README.md", "package.json", "pyproject.toml"]

# Status ordering for "worst wins". NA is excluded from the verdict.
ORDER = {"NA": 0, "GREEN": 1, "YELLOW": 2, "RED": 3}

Result = namedtuple("Result", "name side status headline detail")


already_emitted = ritededup.already_emitted


def is_project_shaped(d, cfg):
    """Does this directory look like a project? Markers come from config, never from code."""
    markers = cfg.get("project_markers") or DEFAULT_PROJECT_MARKERS
    return any((d / m).exists() for m in markers)


# ─── config ─────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "thresholds": {"disk_warn_pct": 85, "disk_crit_pct": 95, "log_age_warn_days": 30,
                   "hook_dedup_window_s": 20},
    "disk_mounts": ["/", "/home", "/mnt/storage"],
    "checks": {},
    "caveats": [],
    "remotes": [],
    "project_markers": list(DEFAULT_PROJECT_MARKERS),
}


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    if CONFIG_PATH.exists():
        try:
            data = riteyaml.load(CONFIG_PATH.read_text(encoding="utf-8"),
                                 str(CONFIG_PATH)) or {}
        except Exception:
            # A malformed config must not stop the session POST. The defaults still run and
            # the report says which checks used them.
            data = {}
        for key in DEFAULT_CONFIG:
            if key in data and data[key] is not None:
                if isinstance(DEFAULT_CONFIG[key], dict) and isinstance(data[key], dict):
                    cfg[key].update(data[key])
                else:
                    cfg[key] = data[key]
    return cfg


TEMPLATE_CONFIG = HERE.parent / "template" / "checks.yaml"


def init_config():
    """Write the documented default config, if there is not one already.

    WHY THIS EXISTS: template/checks.yaml shipped with the port and nothing installed it, so a
    user got the shipped defaults and never learned the file existed — or that `command:` checks
    were available at all. rite_init.py could not do it: that seeds a PROJECT, and this is
    user-level config under ${CLAUDE_PLUGIN_DATA}.

    NEVER OVERWRITES. The same rule the scaffolder follows: an existing file is reported and
    left alone, because a config the user has edited is theirs.
    """
    if ritefs.exists_exactly(CONFIG_PATH):
        print(f"exists, unchanged: {CONFIG_PATH}")
        return 0
    if not ritefs.exists_exactly(TEMPLATE_CONFIG):
        print(f"FAIL  the shipped default is missing: {TEMPLATE_CONFIG}", file=sys.stderr)
        return 1
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(TEMPLATE_CONFIG.read_text(encoding="utf-8"),
                           encoding="utf-8", newline="\n")
    print(f"wrote {CONFIG_PATH}")
    print("Every value in it is optional — deleting the file restores the shipped defaults.")
    return 0


# ─── context passed to each check ───────────────────────────────────────────

class Ctx:
    def __init__(self, cwd, cfg):
        self.cwd = cwd
        self.cfg = cfg
        self.thr = cfg["thresholds"]
        self._mcp_lines = None  # lazy cache for `claude mcp list`

    def mcp_lines(self):
        if self._mcp_lines is None:
            try:
                out = subprocess.run(
                    ["claude", "mcp", "list"], capture_output=True, text=True, timeout=20,
                    encoding="utf-8", errors="replace").stdout
                self._mcp_lines = out.splitlines()
            except Exception:
                self._mcp_lines = []
        return self._mcp_lines


# ─── helpers ────────────────────────────────────────────────────────────────

def _read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def dash_map(path):
    """cwd -> ~/.claude/projects/<path-with-slashes-as-dashes> session dir name."""
    return str(path).replace("/", "-")


def _ppid(pid):
    stat = _read(Path("/proc") / str(pid) / "stat")
    if not stat:
        return None
    # comm field is in parens and may contain spaces/parens; ppid is the field
    # right after the closing paren + state char.
    rp = stat.rfind(")")
    if rp == -1:
        return None
    try:
        return int(stat[rp + 2:].split()[1])
    except (IndexError, ValueError):
        return None


PROC = Path("/proc")


def _all_procs():
    """Snapshot {pid: (ppid, comm, cmdline)} for every process on the machine.

    Linux only. macOS and Windows have no /proc, and the caller reports NA there rather than
    raising — a check that cannot run must never look like a check that passed.
    """
    procs = {}
    if not PROC.is_dir():
        return procs
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        pid = int(p.name)
        comm = _read(p / "comm").strip()
        if not comm:
            continue
        cmdline = _read(p / "cmdline").replace("\x00", " ").strip()
        procs[pid] = (_ppid(pid), comm, cmdline)
    return procs


# ═══ LOCAL TIER ══════════════════════════════════════════════════════════════

# An interactive Claude session reads user input as a stream; subagents and the
# background agent daemon do not. This flag is the discriminator.
_INTERACTIVE_MARKER = "--input-format"


def check_parallel_claude(ctx):
    """RED only if a *separate interactive* claude session is running (race class).

    Excludes this session's own claude and everything it spawned (subagents,
    workers) by walking the process tree, and ignores non-interactive `claude`
    processes such as the background agent daemon. So one VS Code window with
    subagents in flight reads GREEN; a genuinely independent session reads RED.
    """
    procs = _all_procs()
    if not procs:
        return Result("parallel_claude", "claude", "NA",
                      "no /proc on this platform — cannot enumerate sessions", "")
    children = {}
    for pid, (ppid, _, _) in procs.items():
        children.setdefault(ppid, []).append(pid)

    # My ancestor chain, and the nearest claude ancestor = this session's claude.
    mine, cur, session_claude = set(), os.getpid(), None
    while cur and cur in procs and cur not in mine:
        mine.add(cur)
        if session_claude is None and procs[cur][1] == "claude":
            session_claude = cur
        cur = procs[cur][0]

    # Everything spawned under this session's claude (subagents/workers).
    subtree = set()
    if session_claude is not None:
        stack = [session_claude]
        while stack:
            node = stack.pop()
            for c in children.get(node, []):
                if c not in subtree:
                    subtree.add(c)
                    stack.append(c)

    # Reload-twins: when a conversation reloads, the outgoing claude briefly
    # coexists with the new one. Both are children of the same VS Code extension
    # host, so they share this session's claude parent (ppid). A genuinely
    # separate VS Code window has a different extension-host parent. Exclude
    # same-parent siblings to avoid the reload-race false positive.
    session_parent = procs[session_claude][0] if session_claude is not None else None

    excluded = mine | subtree
    others = [
        pid for pid, (ppid, comm, cmdline) in procs.items()
        if comm == "claude" and pid not in excluded
        and _INTERACTIVE_MARKER in cmdline
        and not (session_parent is not None and ppid == session_parent)
    ]
    if others:
        return Result("parallel_claude", "claude", "RED",
                      f"{len(others)} other interactive claude session(s) (PIDs {sorted(others)})",
                      "A separate interactive session can clobber the same files "
                      "(2026-05-14 / 2026-05-27 race class). This session's own "
                      "subagents and the background daemon are excluded. Close the "
                      "other session(s) or confirm they're intended before acting.")
    return Result("parallel_claude", "claude", "GREEN",
                  "no other interactive claude sessions", "")


def check_context_files(ctx):
    """Files that SHOULD load into context exist & are non-empty."""
    missing, present = [], []
    # global CLAUDE.md is mandatory
    if GLOBAL_CLAUDE_MD.exists() and GLOBAL_CLAUDE_MD.stat().st_size > 0:
        present.append("~/.claude/CLAUDE.md")
    else:
        return Result("context_files", "claude", "RED",
                      "global ~/.claude/CLAUDE.md missing or empty",
                      "Global instructions did not load — the harness is misconfigured.")
    if GLOBAL_MEMORY_INDEX.exists():
        present.append("MEMORY.md")
    else:
        missing.append("MEMORY.md")
    proj_md = ctx.cwd / "CLAUDE.md"
    proj_shaped = is_project_shaped(ctx.cwd, ctx.cfg)
    if proj_md.exists():
        present.append("project CLAUDE.md")
    elif proj_shaped:
        missing.append("project CLAUDE.md")
    if missing:
        return Result("context_files", "claude", "YELLOW",
                      "missing: " + ", ".join(missing),
                      "Present: " + ", ".join(present))
    return Result("context_files", "claude", "GREEN",
                  ", ".join(present) + " present", "")


def check_settings_valid(ctx):
    """settings.json parses; any hook command paths it references exist."""
    if not SETTINGS_JSON.exists():
        return Result("settings_valid", "claude", "YELLOW",
                      "settings.json missing", "")
    try:
        data = json.loads(_read(SETTINGS_JSON))
    except Exception as e:
        return Result("settings_valid", "claude", "RED",
                      "settings.json is invalid JSON",
                      f"{e} — hooks/permissions will not load.")
    bad = []
    for grp in (data.get("hooks") or {}).values():
        for entry in grp:
            for h in entry.get("hooks", []):
                cmd = h.get("command", "")
                # first token that looks like an absolute path to a file
                for tok in cmd.split():
                    if tok.startswith("/") and not Path(tok).exists():
                        bad.append(tok)
    if bad:
        return Result("settings_valid", "claude", "YELLOW",
                      "hook command path(s) not found: " + ", ".join(sorted(set(bad))),
                      "A configured hook points at a missing file.")
    return Result("settings_valid", "claude", "GREEN", "valid; hook paths resolve", "")


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, timeout=10,
                          encoding="utf-8", errors="replace")


def check_git_status(ctx):
    inside = _git(ctx.cwd, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return Result("git_status", "project", "NA", "not a git repo", "")
    branch = _git(ctx.cwd, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    dirty = [ln for ln in _git(ctx.cwd, "status", "--porcelain").stdout.splitlines() if ln]
    ahead = behind = 0
    cnt = _git(ctx.cwd, "rev-list", "--left-right", "--count", "@{u}...HEAD")
    if cnt.returncode == 0 and cnt.stdout.strip():
        try:
            behind, ahead = (int(x) for x in cnt.stdout.split())
        except ValueError:
            pass
    flags = []
    if dirty:
        flags.append(f"{len(dirty)} uncommitted")
    if ahead:
        flags.append(f"{ahead} ahead")
    if behind:
        flags.append(f"{behind} behind")
    if flags:
        return Result("git_status", "project", "YELLOW",
                      f"{branch}: " + ", ".join(flags),
                      "\n".join(dirty[:10]))
    return Result("git_status", "project", "GREEN", f"{branch}: clean", "")


def check_disk(ctx):
    mounts = ctx.cfg["disk_mounts"]
    warn, crit = ctx.thr["disk_warn_pct"], ctx.thr["disk_crit_pct"]
    try:
        out = subprocess.run(["df", "-P", *mounts], capture_output=True, text=True,
                             timeout=10, encoding="utf-8", errors="replace").stdout
    except Exception:
        return Result("disk", "machine", "NA", "df unavailable", "")
    worst, lines, status, seen = "GREEN", [], "GREEN", set()
    for ln in out.splitlines()[1:]:
        parts = ln.split()
        if len(parts) < 6:
            continue
        pct = int(parts[4].rstrip("%"))
        mnt = parts[5]
        if mnt in seen:  # `/` and `/home` can resolve to the same filesystem
            continue
        seen.add(mnt)
        lines.append(f"{mnt} {pct}%")
        s = "RED" if pct >= crit else "YELLOW" if pct >= warn else "GREEN"
        if ORDER[s] > ORDER[status]:
            status, worst = s, f"{mnt} at {pct}%"
    if status == "GREEN":
        return Result("disk", "machine", "GREEN", "; ".join(lines), "")
    return Result("disk", "machine", status, worst, "; ".join(lines))


def _vscode_state_blob():
    """Raw bytes of VS Code's global state DB, or None.

    Deliberately engine-free: python3 has sqlite3 built in, but the sibling reader in
    claude-persistent's extension cannot use one (node:sqlite is absent on Node 20), and both
    should agree. SQLite stores short text values verbatim in the page bytes, so a bounded
    regex finds them without opening the file as a database — read-only, no locking.

    LOST AND RESTORED during the port: it sat between two checks that were deliberately not
    ported, and cutting them by span took it too. The engine still RAN — the checker reported
    "check raised: name '_vscode_state_blob' is not defined" as a YELLOW, exactly as its
    per-check exception guard promises. A crash would have been louder and easier; a degraded
    check that keeps running is the failure mode worth having a guard for.
    """
    db = HOME / ".config" / "Code" / "User" / "globalStorage" / "state.vscdb"
    if not db.exists():
        return None
    try:
        return db.read_bytes().decode("latin1")
    except OSError:
        return None


def check_thinking_level(ctx):
    """Thinking on/off, read from VS Code's own state DB (not inferred).

    Costin toggled thinking off mid-session on 2026-09-06 without noticing (two
    set_thinking_level events 22s apart) and worked on hook-dispatch semantics with
    it off. Surfacing it at session start makes that visible instead of silent.
    """
    val = _vscode_state_blob()
    if not val:
        return Result("thinking_level", "claude", "NA", "VS Code state DB unreadable", "")
    m = re.search(r'"thinkingLevel"\s*:\s*"([^"]{0,20})"', val)
    if not m:
        return Result("thinking_level", "claude", "NA", "thinkingLevel not recorded yet", "")
    level = m.group(1)
    if level == "off":
        return Result("thinking_level", "claude", "YELLOW", "thinking is OFF",
                      "Toggle it on for design/debugging work if that wasn't deliberate. "
                      "Note: VS Code flushes this setting to disk lazily (variable — up to "
                      "~a minute observed), so a very recent toggle may not show yet.")
    return Result("thinking_level", "claude", "GREEN", f"thinking: {level}", "")


def check_context_window(ctx):
    """Flag when the reported context window contradicts the model's variant.

    The transcript records the bare id (claude-opus-5) even when the harness
    dispatches claude-opus-5[1m] at ~980K, so anything reading only the transcript
    (e.g. the claude-persistent panel) can understate the window by 5x. If a
    contextWindows override exists in VS Code settings it is authoritative; the
    check only warns when the default would be used for a model we know has a
    long-context variant.
    """
    settings = HOME / ".config" / "Code" / "User" / "settings.json"
    if not settings.exists():
        return Result("context_window", "claude", "NA", "no VS Code settings.json", "")
    try:
        cfg = json.loads(re.sub(r"^\s*//.*$", "", _read(settings), flags=re.M))
    except Exception:
        return Result("context_window", "claude", "NA", "settings.json not parseable", "")
    wins = cfg.get("claudePersistent.contextWindows")
    if not isinstance(wins, dict):
        return Result("context_window", "claude", "NA", "claude-persistent not configured", "")
    overrides = {k: v for k, v in wins.items() if k != "default"}
    if not overrides:
        return Result("context_window", "claude", "YELLOW",
                      "context windows: only a default is set",
                      "Long-context variants (…[1m]) will be reported at the default. "
                      "Add a per-model entry to claudePersistent.contextWindows.")
    return Result("context_window", "claude", "GREEN",
                  "context windows set for: " + ", ".join(sorted(overrides)), "")


def check_caveats(ctx):
    """Static machine caveats — report-only, NA so it never moves the verdict."""
    caveats = ctx.cfg.get("caveats") or []
    if not caveats:
        return Result("caveats", "machine", "NA", "none configured", "")
    return Result("caveats", "machine", "NA", f"{len(caveats)} known caveat(s)",
                  "\n".join(f"- {c}" for c in caveats))


# ═══ NETWORK TIER (--full only) ══════════════════════════════════════════════

def _parse_mcp(ctx):
    """Return {name: (kind, connected_bool, raw)} from `claude mcp list`."""
    res = {}
    for ln in ctx.mcp_lines():
        m = re.match(r"^([^:]+):\s+(.*)$", ln)
        if not m:
            continue
        name, rest = m.group(1).strip(), m.group(2)
        connected = "✓" in rest or "Connected" in rest
        res[name] = (rest, connected)
    return res


def check_mcp_reachable(ctx):
    mcps = _parse_mcp(ctx)
    local = {n: v for n, v in mcps.items() if "claude.ai" not in n.lower()}
    if not local:
        return Result("mcp_reachable", "claude", "NA", "no local MCP servers configured", "")
    down = [n for n, (_, ok) in local.items() if not ok]
    if down:
        return Result("mcp_reachable", "claude", "RED",
                      "unreachable MCP: " + ", ".join(down),
                      "Tool calls against these will fail until restored.")
    return Result("mcp_reachable", "claude", "GREEN",
                  "connected: " + ", ".join(local), "")


def check_google_auth(ctx):
    mcps = _parse_mcp(ctx)
    google = {n: v for n, v in mcps.items() if "claude.ai" in n.lower()}
    if not google:
        return Result("google_auth", "claude", "NA", "no Google MCP servers", "")
    needs = [n for n, (raw, ok) in google.items()
             if not ok or "auth" in raw.lower()]
    if needs:
        return Result("google_auth", "claude", "YELLOW",
                      "needs authentication: " + ", ".join(needs),
                      "Run the authenticate flow if you need Gmail/Calendar/Drive.")
    return Result("google_auth", "claude", "GREEN", "authenticated", "")


def check_remote_reachable(ctx):
    for r in ctx.cfg.get("remotes") or []:
        prefix = Path(os.path.expanduser(r.get("prefix", ""))).resolve()
        try:
            ctx.cwd.relative_to(prefix)
        except ValueError:
            continue
        cmd = r.get("cmd", "")
        timeout = r.get("timeout", 10)
        try:
            p = subprocess.run(cmd, shell=True, cwd=str(ctx.cwd),
                               capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return Result("remote_reachable", "project", "RED",
                          f"remote probe timed out after {timeout}s",
                          f"cmd: {cmd}")
        if p.returncode != 0:
            return Result("remote_reachable", "project", "RED",
                          f"remote probe failed (exit {p.returncode})",
                          f"cmd: {cmd}\n{(p.stderr or p.stdout).strip()[:300]}")
        return Result("remote_reachable", "project", "GREEN",
                      f"remote reachable ({cmd})", "")
    return Result("remote_reachable", "project", "NA", "no remote configured for cwd", "")


# ─── registry: name -> (func, tier) ─────────────────────────────────────────

# NOT IN THIS LIST, AND THAT IS DELIBERATE — restoring any of the three is a regression:
#   mirror_drift        superseded by Rite's mirror_not_stale, which reads the sync stamp
#                       through a predicate shared with the copier. The original compared
#                       mtimes, which this project calls mtime theatre by name.
#   last_log_age        superseded by newest_entry_within_days_of_activity.
#   tracker_registered  reads project-tracker's projects.yaml, which the engine must not know
#                       about (d-project-tracker-stays-separate). It survives as a `command:`
#                       check in the user's own checks.yaml — see run_command_check.
REGISTRY = [
    ("parallel_claude", check_parallel_claude, "local"),
    ("context_files", check_context_files, "local"),
    ("settings_valid", check_settings_valid, "local"),
    ("git_status", check_git_status, "local"),
    ("disk", check_disk, "local"),
    ("thinking_level", check_thinking_level, "local"),
    ("context_window", check_context_window, "local"),
    ("caveats", check_caveats, "local"),
    ("mcp_reachable", check_mcp_reachable, "full"),
    ("google_auth", check_google_auth, "full"),
    ("remote_reachable", check_remote_reachable, "full"),
]


# ── user-declared checks ─────────────────────────────────────────────────────
# THE CLAUSE THAT MAKES d-preflight-is-config-not-fork WORK: "plus checks too personal to
# publish." A check whose config carries a `command:` runs an external program instead of
# engine code, so a check that reads another project's files — or anything a user would never
# publish — needs no place in the engine at all.
#
#   checks:
#     tracker_registered:
#       command: ~/projects/project-tracker/bin/registered.py
#       side: project
#       timeout: 5
#
# The exit code IS the verdict. Anything else is YELLOW naming the check: a hook must not break
# the session it serves, and a check that vanished must never look like a check that passed.
EXIT_STATUS = {0: "GREEN", 1: "YELLOW", 2: "RED", 3: "NA"}


def run_command_check(name, spec, ctx):
    cmd = str(spec.get("command", "")).strip()
    side = spec.get("side", "project")
    if side not in ("claude", "project", "machine"):
        return Result(name, "?", "YELLOW", f"declares an unknown side {side!r}", "")
    if not cmd:
        return Result(name, side, "YELLOW", "declares no command", "")
    target = Path(cmd.split()[0]).expanduser()
    if not ritefs.exists_exactly(target):
        return Result(name, side, "YELLOW", f"command not found: {target}",
                      "Declared in checks.yaml but absent on this machine.")
    try:
        out = subprocess.run([str(target), *cmd.split()[1:]], capture_output=True, text=True,
                             timeout=float(spec.get("timeout", 10)), cwd=str(ctx.cwd),
                             encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return Result(name, side, "YELLOW", f"timed out after {spec.get('timeout', 10)}s", "")
    except OSError as e:
        return Result(name, side, "YELLOW", f"could not run: {e}", "")
    lines = [ln for ln in (out.stdout or "").splitlines() if ln.strip()]
    headline = lines[0] if lines else f"exit {out.returncode}"
    detail = "\n".join(lines[1:])
    status = EXIT_STATUS.get(out.returncode)
    if status is None:
        return Result(name, side, "YELLOW",
                      f"exit {out.returncode} is not one of 0/1/2/3", headline)
    return Result(name, side, status, headline, detail)


def run_checks(ctx, include_network):
    enabled = ctx.cfg.get("checks") or {}
    results = []
    for name, func, tier in REGISTRY:
        if enabled.get(name, True) is False:
            continue
        if tier == "full" and not include_network:
            continue
        try:
            results.append(func(ctx))
        except Exception as e:
            results.append(Result(name, "?", "YELLOW", f"check raised: {e}", ""))
    # User-declared checks run after the built-ins, in declaration order. A name that collides
    # with a built-in is ignored rather than silently shadowing it — the engine's own checks are
    # not overridable, only switchable.
    built_in = {n for n, _, _ in REGISTRY}
    for name, spec in enabled.items():
        if not isinstance(spec, dict) or name in built_in:
            continue
        try:
            results.append(run_command_check(name, spec, ctx))
        except Exception as e:
            results.append(Result(name, "?", "YELLOW", f"check raised: {e}", ""))
    return results


def verdict_of(results):
    worst = "GREEN"
    for r in results:
        if ORDER[r.status] > ORDER[worst]:
            worst = r.status
    return worst


# ─── output ─────────────────────────────────────────────────────────────────

GLYPH = {"GREEN": "✓", "YELLOW": "▲", "RED": "✗", "NA": "·"}


def write_report(ctx, results, verdict, include_network):
    now = dt.datetime.now()
    lines = [
        f"rite preflight POST — {now:%Y-%m-%d %H:%M}",
        f"cwd:     {ctx.cwd}",
        f"tier:    {'local+network' if include_network else 'local'}",
        f"VERDICT: {verdict}",
        "",
    ]
    for r in results:
        lines.append(f"{GLYPH[r.status]} {r.status:<6} {r.name:<20} [{r.side}]  {r.headline}")
        if r.detail:
            for dl in r.detail.splitlines():
                lines.append(f"        {dl}")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def print_human(ctx, results, verdict, include_network):
    print(f"rite preflight POST — {dt.datetime.now():%Y-%m-%d %H:%M}  ({ctx.cwd})")
    print(f"VERDICT: {verdict}  [tier: {'local+network' if include_network else 'local'}]")
    print()
    for r in results:
        print(f"{GLYPH[r.status]} {r.status:<6} {r.name:<20} [{r.side}]  {r.headline}")
        if r.detail:
            for dl in r.detail.splitlines():
                print(f"        {dl}")
    print(f"\nfull report: {REPORT_PATH}")


def verdict_text(results, verdict):
    """The compact verdict, without the JSON envelope or the relay line.

    Split out during the port so rite_session_start.py can fold this into its single
    additionalContext emission. Two hooks each printing their own JSON is what the port
    replaces — the user had one line from preflight and one from rite, describing one session.
    """
    now = dt.datetime.now()
    n = sum(1 for r in results if r.status != "NA")
    if verdict == "GREEN":
        return f"preflight GREEN — {n} checks ok ({now:%H:%M})"
    out = [f"preflight {verdict} — session POST ({now:%H:%M}):"]
    for r in results:
        if r.status in ("YELLOW", "RED"):
            out.append(f"  [{r.status}/{r.side}] {r.name}: {r.headline}")
    out.append(f"full report: {REPORT_PATH}")
    return "\n".join(out)


def local_verdict(cwd):
    """Run the local tier for `cwd` and return (text, verdict). Never raises.

    The entry point rite_session_start.py uses. A session POST that throws would block the
    session it exists to inform, so every failure degrades to no text at all.
    """
    try:
        cfg = load_config()
        ctx = Ctx(cwd, cfg)
        results = run_checks(ctx, include_network=False)
        if not results:
            return None, "GREEN"
        verdict = verdict_of(results)
        write_report(ctx, results, verdict, False)
        return verdict_text(results, verdict), verdict
    except Exception:
        return None, "GREEN"


def emit_hook(results, verdict):
    now = dt.datetime.now()
    n = sum(1 for r in results if r.status != "NA")
    if verdict == "GREEN":
        ctx_text = f"preflight GREEN — {n} checks ok ({now:%H:%M})"
    else:
        out = [f"preflight {verdict} — session POST ({now:%H:%M}):"]
        for r in results:
            if r.status in ("YELLOW", "RED"):
                out.append(f"  [{r.status}/{r.side}] {r.name}: {r.headline}")
        out.append(f"full report: {REPORT_PATH}")
        ctx_text = "\n".join(out)
    # SessionStart cannot pop a message straight to the user (systemMessage is not
    # honored for this event). The one honest channel is additionalContext -> Claude;
    # the relay line makes Claude state the verdict at the top of its first reply.
    # For an on-request, fully-visible report, run the /preflight command instead.
    relay = ("\n(Claude: open your first reply by stating this preflight verdict to "
             "Costin, before anything else.)")
    # Source-verified 2026-05-29 (read anthropic.claude-code v2.1.156 on disk): the VS
    # Code extension consumes ONLY `additionalContext` (1 ref). `systemMessage`,
    # `showOutput`, `suppressOutput` have 0 refs — they do nothing in the extension. The
    # banner above the prompt (rateLimitWarning/warningBanner/...) is built-in and not
    # hook-addressable. So additionalContext + a relay instruction is the only path that
    # can reach the user in the VS Code chat; /preflight covers the on-demand case.
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": ctx_text + relay,
    }}))


# ─── main ───────────────────────────────────────────────────────────────────

def read_payload(hook_mode):
    """Hook mode: the SessionStart JSON payload from stdin (session_id, source, cwd).

    Read once — stdin is a stream and cannot be re-read by the dedup below.
    """
    if not hook_mode:
        return {}
    try:
        return json.loads(sys.stdin.read() or "{}") or {}
    except Exception:
        return {}


def resolve_cwd(hook_mode, payload):
    if hook_mode:
        if payload.get("cwd"):
            return Path(payload["cwd"]).resolve()
        env = os.environ.get("CLAUDE_PROJECT_DIR")
        if env:
            return Path(env).resolve()
    return Path.cwd().resolve()


def main():
    ap = argparse.ArgumentParser(description="rite — the session POST (power-on self-test)")
    ap.add_argument("--hook", action="store_true",
                    help="hook mode: emit verdict JSON for additionalContext")
    ap.add_argument("--init-config", action="store_true",
                    help="write the documented default checks.yaml if absent; never overwrites")
    ap.add_argument("--full", action="store_true",
                    help="include the network tier (manual runs)")
    args = ap.parse_args()

    if args.init_config:
        return init_config()

    cfg = load_config()
    payload = read_payload(args.hook)
    cwd = resolve_cwd(args.hook, payload)

    # Duplicate dispatch of the same SessionStart: stay silent (emit nothing) and
    # skip the checks entirely — the first firing already wrote last-post.txt.
    # Wrapped: a bug in the dedup path must never cost us the verdict, so any
    # failure here falls through and emits (fail-open, same as the helper).
    if args.hook:
        try:
            if already_emitted(payload, cwd,
                               cfg["thresholds"].get("hook_dedup_window_s", 20),
                               STAMP_PATH):
                sys.exit(0)
        except SystemExit:
            raise
        except Exception:
            pass

    ctx = Ctx(cwd, cfg)
    include_network = args.full and not args.hook  # network never runs in the auto hook
    results = run_checks(ctx, include_network)
    verdict = verdict_of(results)

    write_report(ctx, results, verdict, include_network)
    if args.hook:
        emit_hook(results, verdict)
    else:
        print_human(ctx, results, verdict, include_network)
    sys.exit(0)  # never block the session


if __name__ == "__main__":
    sys.exit(main() or 0)
