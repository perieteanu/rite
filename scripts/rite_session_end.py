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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rite_copy  # noqa: E402
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()


def copy_everything(root: Path) -> None:
    """Mirror memory, copy plans, copy this session's scratchpad scripts.

    IN-PROCESS, not a subprocess. Until 2026-09-10 this shelled out to
    ~/.claude/scripts/claude-mirror-memory.py, which was the right call while that script was
    the only implementation — "a second implementation is drift, not robustness". It is no
    longer the only one: rite_copy.py is the port, so calling it directly removes both the
    subprocess and the dependency on a file outside the plugin.

    THE SCRIPTS ARE THE URGENT ONE. Plans and memory live under ~/.claude and survive; the
    scratchpad is under /tmp and does not survive a reboot. For those, late is the same as
    never, which is why this runs here — SessionEnd fires whether or not anyone remembers to
    type /rite:end.

    Silent and total: SessionEnd has no turns left, so nothing printed here reaches anyone, and
    one copier failing must not stop the next two.
    """
    for action in (rite_copy.mirror_memory, rite_copy.copy_plans, rite_copy.copy_scripts):
        try:
            action(root, False)
        except Exception:
            # A hook that raises is a hook that breaks the session it was meant to serve.
            continue


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    root = Path(payload.get("cwd") or os.getcwd()).resolve()
    if not ritefs.marker_present(root):
        return 0
    copy_everything(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
