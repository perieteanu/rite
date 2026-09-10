import pathlib, sys
p = pathlib.Path("scripts/rite_watch.py")
t = p.read_text(encoding="utf-8")

# 1 — the cwd half
anchor = "def main() -> int:"
new = '''# ── mid-session project switch ───────────────────────────────────────────────
# CwdChanged fires on EVERY directory change, including a cd into a subdirectory of the same
# project, and it has no matcher support. Flagging all of them would be noise, and a noisy
# watcher is a disabled watcher. The signal worth reporting is narrower: the session has moved
# to a DIFFERENT project.
#
# WHY IT IS WORTH REPORTING AT ALL: Rite assumes one project per session and has never said so
# anywhere. Every artifact it writes — LOG.md, HANDOFF.md, the copiers' destinations — is
# resolved from one root. A session that changes project mid-way will write half its record in
# one place and half in another, and nothing today notices.

def project_root_of(path: Path) -> Path | None:
    """The nearest ancestor carrying a .rite.yaml marker, or None."""
    for candidate in [path, *path.parents]:
        if ritefs.marker_present(candidate):
            return candidate
    return None


def switch_stamp() -> Path:
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    return Path(base or (Path.home() / ".claude" / "rite")) / ".session-project.json"


def on_cwd_changed(payload: dict) -> int:
    session = str(payload.get("session_id") or "")
    new_cwd = payload.get("cwd")
    if not session or not isinstance(new_cwd, str):
        return 0
    root = project_root_of(Path(new_cwd).resolve())
    if root is None:
        return 0  # left rite-managed ground entirely; not ours to police

    stamp = switch_stamp()
    try:
        seen = json.loads(stamp.read_text(encoding="utf-8")) if stamp.is_file() else {}
    except (OSError, ValueError):
        seen = {}

    first = seen.get(session)
    if first is None:
        # First rite project this session has seen. Record it and stay silent.
        seen = {session: str(root)}   # one session per stamp; old entries are not history
        try:
            stamp.parent.mkdir(parents=True, exist_ok=True)
            stamp.write_text(json.dumps(seen), encoding="utf-8", newline="\\n")
        except OSError:
            pass
        return 0

    if first == str(root) or seen.get(session + ":reported"):
        return 0  # same project, or already said once

    try:
        seen[session + ":reported"] = True
        stamp.write_text(json.dumps(seen), encoding="utf-8", newline="\\n")
    except OSError:
        pass

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "CwdChanged",
        "additionalContext": (
            f"rite — this session started in {Path(first).name} and has moved to {root.name}. "
            f"Rite resolves LOG.md, HANDOFF.md and every copy destination from ONE project "
            f"root, so a session spanning two will split its record between them. Close the "
            f"first properly, or treat this as a second session. Reported once."
        ),
    }}))
    return 0


def main() -> int:'''
if t.count(anchor) != 1:
    sys.exit("ABORT anchor")
t = t.replace(anchor, new, 1)

# 2 — dispatch on the event
old_body = '''    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, TypeError):
        return 0

    tool = payload.get("tool_input")'''
new_body = '''    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, TypeError):
        return 0

    # ONE ENTRY POINT, DISPATCHING ON THE EVENT. Both halves are "what Rite notices while the
    # session runs", and a second script would duplicate the payload handling and the
    # never-raise discipline for no gain.
    if payload.get("hook_event_name") == "CwdChanged":
        try:
            return on_cwd_changed(payload)
        except Exception:
            return 0

    tool = payload.get("tool_input")'''
if t.count(old_body) != 1:
    sys.exit("ABORT body")
t = t.replace(old_body, new_body, 1)
t = t.replace('"""rite_watch — the PostToolUse watcher. What Rite notices while the session is still running.',
              '"""rite_watch — the watcher. What Rite notices while the session is still running.', 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("cwd half added")
