#!/usr/bin/env python3
"""Contract test: the SessionStart hook's output must be SHAPED so the harness reads it.

This test exists because of a real failure, not a hypothetical one. On 2026-09-08 the hook
emitted a top-level `additionalContext` key instead of nesting it under `hookSpecificOutput`.
It ran, exited 0, produced valid JSON, and was logged by the harness as `success` — while
reaching nobody. Nothing failed. That is the exact class of silent non-enforcement this whole
project exists to convert into a check that fails.

So the assertion is deliberately about SHAPE, not about content. A verdict that is correct and
unreadable is worth nothing, and only the shape distinguishes the two.

Run:  python3 scripts/test-hook-output.py
Exit: 0 pass · 1 fail
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
MARKER = ".rite.yaml"

# The harness reads exactly this path out of the hook's stdout. Verified against the shipped
# 2.1.263 extension log, and matched against claude-preflight, whose hook demonstrably lands.
ENVELOPE = "hookSpecificOutput"
EVENT_FIELD = "hookEventName"
CONTEXT_FIELD = "additionalContext"
EVENT_NAME = "SessionStart"

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def run_hook(cwd: pathlib.Path) -> str:
    """Invoke the hook the way the harness does: through the launcher shim, payload on stdin.

    Going through the shim rather than importing the module keeps the test honest about the
    thing that actually runs, and covers the shim's action dispatch at the same time.
    """
    if os.name == "nt":
        cmd = ["powershell", "-NoProfile", "-File", str(ROOT / "hooks" / "rite.ps1"),
               "session-start"]
    else:
        cmd = ["bash", str(ROOT / "hooks" / "rite.sh"), "session-start"]
    payload = json.dumps({
        "hook_event_name": EVENT_NAME,
        "source": "startup",
        "cwd": str(cwd),
        "session_id": "test-hook-output",
    })
    out = subprocess.run(cmd, input=payload, capture_output=True, text=True,
                         encoding="utf-8", cwd=str(ROOT))
    if out.returncode != 0:
        fail(f"shim exited {out.returncode} for cwd={cwd}: {out.stderr.strip()[:200]}")
    return out.stdout


# 1. An opted-in project must produce a verdict the harness can actually read.
raw = run_hook(ROOT)
body = raw.strip()
if not body:
    fail("no output for an opted-in project — rite's own repo carries a .rite.yaml marker")
else:
    try:
        doc = json.loads(body)
    except ValueError as exc:
        doc = None
        fail(f"stdout is not valid JSON: {exc}")

    if isinstance(doc, dict):
        # The regression itself. A top-level key is silently discarded by the harness.
        if CONTEXT_FIELD in doc:
            fail(f"top-level {CONTEXT_FIELD!r} — the harness ignores it and logs success "
                 f"anyway. Nest it under {ENVELOPE!r}.")
        env = doc.get(ENVELOPE)
        if not isinstance(env, dict):
            fail(f"missing {ENVELOPE!r} envelope; got keys {sorted(doc)}")
        else:
            if env.get(EVENT_FIELD) != EVENT_NAME:
                fail(f"{ENVELOPE}.{EVENT_FIELD} is {env.get(EVENT_FIELD)!r}, "
                     f"expected {EVENT_NAME!r}")
            ctx = env.get(CONTEXT_FIELD)
            if not isinstance(ctx, str) or not ctx.strip():
                fail(f"{ENVELOPE}.{CONTEXT_FIELD} is empty or not a string")

# 2. A project that never opted in must stay silent — no envelope, no empty envelope.
with tempfile.TemporaryDirectory() as tmp:
    quiet = run_hook(pathlib.Path(tmp)).strip()
    if quiet:
        fail(f"spoke in a project with no {MARKER}: {quiet[:120]!r}")

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("PASS  hook output is nested under hookSpecificOutput; silent where not invited.")
sys.exit(0)
