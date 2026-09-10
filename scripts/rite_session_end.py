#!/usr/bin/env python3
"""rite_session_end — the mechanical half. No judgement, because there are no turns left.

SessionEnd fires when Claude has no turns remaining. It can copy files and stamp state; it
CANNOT write a handoff, distil a LOG entry, or update docs. Anything needing a decision runs
earlier, from /rite:end. That split is forced by the harness, not chosen.

Deliberately silent: nothing it prints can reach anyone.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()


def mirror_memory(root: Path) -> None:
    """Reuse the existing mirror. A second implementation is drift, not robustness."""
    script = Path.home() / ".claude/scripts/claude-mirror-memory.py"
    if not script.is_file():
        return
    try:
        subprocess.run([sys.executable, str(script), "--project", str(root)],
                       capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        pass


def copy_plans(root: Path) -> None:
    """Copy plans out of ~/.claude/plans into docs/PLAN-<date>-<slug>.md.

    NOT IMPLEMENTED. Attribution is the blocker: plan files carry harness-generated names with
    no project in them (cheeky-seeking-clock.md), so a plan cannot be matched to a project
    retrospectively with any confidence. Copying the wrong plan into a project is worse than
    copying none — it would be a document that reads as a record and is false.

    The route that works is copy-on-CREATION via a FileChanged watcher, where the project is
    simply the one the session is in. Tracked as c-plan-attribution; deliberately left undone
    here rather than guessed at.
    """
    return


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    root = Path(payload.get("cwd") or os.getcwd()).resolve()
    if not ritefs.marker_present(root):
        return 0
    mirror_memory(root)
    copy_plans(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
