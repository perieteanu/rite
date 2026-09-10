#!/usr/bin/env python3
"""rite_watch — the PostToolUse watcher. What Rite notices while the session is still running.

THE GAP THIS CLOSES. Every implemented completion test is an end-of-session test, so a session
could rewrite an append-only file at 14:00 and the standard stayed green until it closed. The
protocol's honest_limits said so in as many words. /rite:update made the record correctable
mid-session on demand; this makes one class of damage report ITSELF, at the moment it happens.

WHY THIS ONE WATCHER FIRST, of the eight in mid_term: it is the only one with a measured hit
rate rather than a plausible rationale. ROADMAP records 100% on this project's own real
failures — a milestones entry inserted mid-list, and roughly thirty LOG entries with
extrapolated timestamps, some ahead of real time.

WHAT IT CHECKS, both against predicates the checker already uses:

  1. APPEND-ONLY DISCIPLINE — a write that removes or changes an existing line in a file the
     standard declares append_only. Measured against git HEAD, so it needs no state of its own
     and cannot be fooled by a second write.
  2. FUTURE LOG TIMESTAMPS — an entry dated later than now, which is what extrapolating from an
     earlier clock reading produces. c-log-timestamps-must-be-machine-read, which has had
     nowhere to run since 2026-09-08.

IT IS SILENT ON SUCCESS, and that is a hard requirement rather than a preference: it fires on
every Write and Edit, and a watcher that speaks when nothing is wrong is one the user disables
within a day. It emits only when it has something to say.

IT ALWAYS EXITS 0. A hook that fails is a hook that breaks the session it was meant to serve.

Run:  rite.sh watch          (PostToolUse; payload on stdin)
Exit: 0, always.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rite_copy  # noqa: E402
import ritefs  # noqa: E402
import riterules  # noqa: E402
import riteyaml  # noqa: E402

ritefs.use_utf8_stdio()

SPEC_PATH = HERE.parent / "spec" / "project-standard.yaml"


def append_only_paths() -> set[str]:
    """Artifacts the standard declares append_only. Read from the spec, never listed here.

    Hardcoding {"LOG.md", "docs/DECISIONS.yaml"} would be a second copy of a declaration the
    spec already owns, and it would go stale the day an artifact's discipline changes.
    """
    try:
        spec = riteyaml.load(SPEC_PATH.read_text(encoding="utf-8"), str(SPEC_PATH))
    except (OSError, riteyaml.RiteYamlError):
        return set()
    return {str(a.get("path")) for a in spec.get("artifacts") or []
            if a.get("write_discipline") == "append_only" and a.get("path")}


def findings_for(root: Path, rel: str) -> list[str]:
    notes: list[str] = []

    if rel in append_only_paths():
        removed = riterules.git_removed_lines(root, rel)
        if removed:
            notes.append(
                f"{rel} is APPEND-ONLY and this write changed or removed {removed} existing "
                f"line(s). Appending is the only legal edit. If a past entry is wrong, append a "
                f"dated correction beneath it — never rewrite it. Check `git diff -- {rel}`."
            )

    if rel.rsplit("/", 1)[-1] == "LOG.md":
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        future = riterules.log_future_timestamps(text)
        if future:
            notes.append(
                f"{rel} carries {len(future)} entry/entries dated in the FUTURE — which is what "
                f"extrapolating from an earlier clock reading produces. Read the machine clock "
                f"for every entry. First: {future[0]}"
            )
    return notes


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, TypeError):
        return 0

    tool = payload.get("tool_input")
    written = tool.get("file_path") if isinstance(tool, dict) else None
    if not isinstance(written, str):
        return 0

    root = Path(payload.get("cwd") or os.getcwd()).resolve()
    # Opt-in, like every other surface. Silent where not invited.
    if not ritefs.marker_present(root):
        return 0

    try:
        rel = Path(written).resolve().relative_to(root).as_posix()
    except ValueError:
        return 0  # written outside the project — not ours to police

    try:
        notes = findings_for(root, rel)
    except Exception:
        # A watcher that raises is a watcher that breaks the write it was watching.
        return 0

    if notes:
        # PLAIN TEXT IS DISCARDED ON TOOL EVENTS — the mechanism note recorded on the roadmap
        # item. additionalContext is the only channel that reaches the model here.
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "rite — write discipline:\n  " + "\n  ".join(notes),
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
