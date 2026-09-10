import pathlib, sys
p = pathlib.Path("scripts/rite_preflight.py")
t = p.read_text(encoding="utf-8")

def sub(old, new, label):
    global t
    if t.count(old) != 1:
        sys.exit(f"ABORT {label}: matched {t.count(old)}")
    t = t.replace(old, new, 1)
    print(f"  ok  {label}")

# 1 — docstring / identity
sub('''"""
preflight.py — claude-preflight session POST (power-on self-test).''',
    '''"""rite_preflight — the session POST (power-on self-test): what is wrong, and whose side it is on.

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
  Restoring any of the three is a regression, not an omission.''',
    "docstring")

# 2 — paths: plugin data, derived slug, no audit module
sub('''HOME = Path.home()
PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_DIR / "checks.yaml"
REPORT_PATH = PROJECT_DIR / "last-post.txt"
# Dedup stamp for the extension's double-dispatched SessionStart (see already_emitted).
# The window itself is configurable in checks.yaml (thresholds.hook_dedup_window_s).
STAMP_PATH = PROJECT_DIR / ".last-hook-stamp.json"
CLAUDE_DIR = HOME / ".claude"
AUDIT_PATH = CLAUDE_DIR / "scripts" / "claude-global-audit.py"
GLOBAL_CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"
SETTINGS_JSON = CLAUDE_DIR / "settings.json"
# Global memory index lives under the home-root session dir (see claude-global-audit).
GLOBAL_MEMORY_INDEX = CLAUDE_DIR / "projects" / "-home-perieteanu" / "memory" / "MEMORY.md"
''',
    '''HERE = Path(__file__).resolve().parent
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
''',
    "paths")

# 3 — drop the audit loader entirely
sub('''# ─── reuse: load the audit module by path (dashed filename) ─────────────────

def load_audit():
    try:
        spec = importlib.util.spec_from_file_location("claude_global_audit", AUDIT_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


AUDIT = load_audit()

# Shared with claude-mirror-memory.py — the other SessionStart hook that injects
# additionalContext and is hit by the same double dispatch.
sys.path.insert(0, str(PROJECT_DIR))
from hookdedup import already_emitted  # noqa: E402
''',
    '''already_emitted = ritededup.already_emitted


def is_project_shaped(d, cfg):
    """Does this directory look like a project? Markers come from config, never from code."""
    markers = cfg.get("project_markers") or DEFAULT_PROJECT_MARKERS
    return any((d / m).exists() for m in markers)
''',
    "audit loader")

p.write_text(t, encoding="utf-8", newline="\n")
print(f"rite_preflight.py: {len(p.read_bytes())} bytes")
