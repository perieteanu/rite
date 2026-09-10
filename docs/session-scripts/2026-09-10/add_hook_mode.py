import pathlib, sys
p = pathlib.Path("scripts/rite_copy.py")
t = p.read_text(encoding="utf-8")

anchor = "def main(argv: list[str]) -> int:"
mode = '''def run_as_hook() -> int:
    """PostToolUse. Refresh the mirror only when a memory file was just written.

    WHY A MODE RATHER THAN JUST RUNNING --memory: a full refresh costs ~66ms, and PostToolUse
    fires on every Write and Edit. Paying that on every edit to catch the handful that touch a
    memory would be a tax on the whole session, and a hook that makes editing feel slow is a
    hook the user removes.

    It replaces the mid-session half of the global claude-mirror-memory hook, which is the only
    thing SessionEnd copying could not cover: end-of-session freshness leaves the mirror wrong
    for the length of the session, and the mirror exists to be READ from the workspace.

    ALWAYS EXITS 0. A hook that fails is a hook that breaks the session it was meant to serve,
    and this one is never worth a lost turn.
    """
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, TypeError):
        return 0
    tool = payload.get("tool_input")
    written = tool.get("file_path") if isinstance(tool, dict) else None
    if not isinstance(written, str):
        return 0
    # A memory file, not the MEMORY.md index — the index is a table of contents and the mirror
    # excludes it, so writing it changes nothing the mirror shows.
    normalised = written.replace("\\\\", "/")
    if "/memory/" not in normalised or normalised.endswith("/MEMORY.md"):
        return 0
    root = Path(payload.get("cwd") or os.getcwd()).resolve()
    if not ritefs.marker_present(root):
        return 0
    try:
        mirror_memory(root, False)
    except Exception:
        pass
    return 0


def main(argv: list[str]) -> int:'''
if t.count(anchor) != 1:
    sys.exit("ABORT")
t = t.replace(anchor, mode, 1)
t = t.replace('    ap.add_argument("-n", "--dry-run", action="store_true", help="report, write nothing")',
              '    ap.add_argument("-n", "--dry-run", action="store_true", help="report, write nothing")\n'
              '    ap.add_argument("--hook", action="store_true",\n'
              '                    help="PostToolUse: refresh the mirror iff a memory file was written")', 1)
t = t.replace("    args = ap.parse_args(argv[1:])\n\n    root =",
              "    args = ap.parse_args(argv[1:])\n\n    if args.hook:\n        return run_as_hook()\n\n    root =", 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("hook mode added")
