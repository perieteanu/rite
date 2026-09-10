#!/usr/bin/env python3
"""rite_session_start — the SessionStart half of the protocol.

Reports, never enforces. `phases.start` declares must_not: block, prompt, or re-run anything
with side effects. Gating belongs to an explicitly invoked checker, not to a hook nobody asked
for.

Reads the hook payload on stdin, emits JSON on stdout with the context nested under
`hookSpecificOutput.additionalContext` — see emit() for why the nesting is load-bearing.
That field is the channel that reaches Claude; `systemMessage` does nothing under
entrypoint=claude-vscode.

Three things:
  1. the project-standard verdict, from rite-check
  2. did the last session close — HANDOFF `written:` against the newest LOG.md entry
  3. the handoff itself: live, or expired/spent and therefore confidently wrong

NAG POLICY: an unclosed previous session is reported ONCE, then never again. A warning that
never clears is the gate that always fails, and a gate that always fails gets switched off.
State lives in ${CLAUDE_PLUGIN_DATA} — the plugin's own storage, which is the declared
exception to never_mutate_claude_home. It is NOT written into HANDOFF, which is write_once and
freezes at session end, and it is NOT a new project artifact.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import riteyaml  # noqa: E402
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

_LOG_TS = re.compile(r"^(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2})(?::(\d{2}))?\s\|")
_FM = re.compile(r"^---\s*\n(.*?)\n---\s*(\n|$)", re.S)


def emit(context: str | None) -> None:
    """One JSON object on stdout. Silence is a valid, common answer.

    The NESTING is load-bearing, not decoration. The harness reads
    `hookSpecificOutput.additionalContext` and ignores a top-level `additionalContext` —
    logging the hook as `success` either way. A bare key therefore exits 0, emits valid
    JSON, and reaches nobody: the exact failure class this project exists to catch.
    Verified 2026-09-08 against the 2.1.263 extension log, where the two working hooks
    each logged `provided additionalContext (N chars)` and this one did not.

    scripts/test-hook-output.py asserts the shape. Do not flatten it.
    """
    if context:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }}, sys.stdout)
    sys.stdout.write("\n")


def newest_log_date(root: Path):
    try:
        text = (root / "LOG.md").read_text(encoding="utf-8")
    except OSError:
        return None
    newest = None
    for line in text.splitlines():
        m = _LOG_TS.match(line)
        if m:
            d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if newest is None or d > newest:
                newest = d
    return newest


def handoff_frontmatter(root: Path):
    try:
        text = (root / "HANDOFF.md").read_text(encoding="utf-8")
    except OSError:
        return None
    m = _FM.match(text)
    if not m:
        return None
    try:
        return riteyaml.load(m.group(1), "HANDOFF.md") or {}
    except riteyaml.RiteYamlError:
        return None


def nag_state_path() -> Path | None:
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    return Path(base) / "nag-state.json" if base else None


def already_nagged(project: str, marker: str) -> bool:
    """True when this exact unclosed-session state was already reported."""
    p = nag_state_path()
    if p is None:
        return False
    try:
        state = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    if state.get(project) == marker:
        return True
    state[project] = marker
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass  # unable to remember is not a reason to fail the session
    return False


def run_checker(root: Path) -> list[str]:
    checker = HERE / "rite-check.py"
    if not checker.is_file():
        return []
    try:
        # encoding + errors are BOTH required, and the second is the subtle one. This decodes
        # the checker's report and then searches it for the literal "checks ·". Left to the
        # locale, Windows decodes cp1252 — where 0xB7 happens to be ·, so the match works by
        # coincidence — while cp437 and cp850 give a different character and the tail line is
        # silently dropped instead of erroring. A verdict quietly missing its summary is worse
        # than one that fails loudly.
        out = subprocess.run([sys.executable, str(checker), str(root)],
                             capture_output=True, text=True, timeout=20,
                             encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return []
    lines = [ln.strip() for ln in out.stdout.splitlines()
             if ln.strip().startswith(("RED", "YELLOW"))]
    tail = [ln.strip() for ln in out.stdout.splitlines() if "checks ·" in ln]
    return lines[:6] + tail


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    root = Path(payload.get("cwd") or os.getcwd()).resolve()

    # Opt-in. Silent where not invited.
    if not ritefs.marker_present(root):
        emit(None)
        return 0

    parts: list[str] = []

    findings = run_checker(root)
    if findings:
        parts.append("rite — project standard:\n  " + "\n  ".join(findings))

    fm = handoff_frontmatter(root)
    newest = newest_log_date(root)
    if fm is not None:
        written = fm.get("written")
        status = str(fm.get("status", "")).lower()
        expires = re.search(r"\d{4}-\d{2}-\d{2}", str(fm.get("expires", "")))
        today = dt.date.today()

        if status == "spent":
            parts.append("rite — HANDOFF.md is marked spent and still present. "
                         "A spent handoff is worse than none: it is confidently wrong.")
        elif expires and dt.date.fromisoformat(expires.group(0)) < today:
            parts.append(f"rite — HANDOFF.md expired on {expires.group(0)}. "
                         "Treat its claims as unverified until refreshed.")

        try:
            wdate = dt.date.fromisoformat(str(written).strip())
        except (ValueError, AttributeError):
            wdate = None
        if wdate and newest and wdate < newest:
            marker = f"{wdate}<{newest}"
            if not already_nagged(str(root), marker):
                parts.append(
                    f"rite — the last session did not close. HANDOFF.md was written {wdate}, "
                    f"but LOG.md runs to {newest}. Work happened after the handoff was last "
                    f"touched. Reported once; this will not be repeated."
                )
    elif (root / "HANDOFF.md").exists():
        parts.append("rite — HANDOFF.md has no parseable front matter, so its expiry and "
                     "session_end outcome cannot be read.")
    else:
        parts.append("rite — no HANDOFF.md. It is tier 0: 'nothing to hand off' is written "
                     "down as genre: none, not left as an absent file.")

    emit("\n\n".join(parts) if parts else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
