#!/usr/bin/env python3
"""ritededup — suppress the VS Code extension's double-dispatched SessionStart.

Ported into Rite 2026-09-10 from claude-preflight's hookdedup.py. Rite's own
SessionStart hook injects `additionalContext` and was never covered by the original,
which guarded only the two hooks registered in settings.json.

Why: the Claude Code VS Code extension dispatches a single SessionStart event
*twice* — verified 2026-09-06 in the extension log, identical `session_id` +
`source`, ~47ms apart. Each hook therefore injected its line into context twice
per session start.

Contract: call `already_emitted(payload, cwd, window_s, stamp_path)` before
emitting. True => this exact event was handled moments ago; emit nothing.

Fail-open by design: no `session_id`, a zero window, or any filesystem error
returns False (emit). A duplicate line is a much cheaper failure than a
silently missing verdict.
"""

import json
import time
from pathlib import Path


def already_emitted(payload, cwd, window_s, stamp_path):
    """True if this SessionStart (session_id+source+cwd) was already handled.

    `window_s` of 0 (or falsy) disables dedup. Each caller passes its own
    `stamp_path` so the two hooks never clobber each other's stamp.
    """
    if not window_s:
        return False
    sid = (payload or {}).get("session_id")
    if not sid:
        return False  # no identity to dedup on — always emit
    key = f"{sid}|{(payload or {}).get('source', '')}|{cwd}"
    stamp = Path(stamp_path)
    try:
        stamp.parent.mkdir(parents=True, exist_ok=True)
        if stamp.exists():
            prev = json.loads(stamp.read_text(encoding="utf-8") or "{}")
            if (prev.get("key") == key
                    and time.time() - float(prev.get("ts", 0)) < window_s):
                return True
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.write_text(json.dumps({"key": key, "ts": time.time()}),
                         encoding="utf-8", newline="\n")
    except Exception:
        return False
    return False
