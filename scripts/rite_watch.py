#!/usr/bin/env python3
"""rite_watch — the watcher. What Rite notices while the session is still running.

THE GAP THIS CLOSES. Every implemented completion test is an end-of-session test, so a session
could rewrite an append-only file at 14:00 and the standard stayed green until it closed. The
protocol's honest_limits said so in as many words. /rite:update made the record correctable
mid-session on demand; this makes one class of damage report ITSELF, at the moment it happens.

WHY THIS ONE WATCHER FIRST, of the eight in mid_term: it is the only one with a measured hit
rate rather than a plausible rationale. ROADMAP records 100% on this project's own real
failures — a milestones entry inserted mid-list, and roughly thirty LOG entries with
extrapolated timestamps, some ahead of real time.

WHAT IT CHECKS, all against predicates the checker already uses:

  1. APPEND-ONLY DISCIPLINE — a write that removes or changes an existing line in a file the
     standard declares append_only. Measured against git HEAD, so it needs no state of its own
     and cannot be fooled by a second write.
  2. FUTURE LOG TIMESTAMPS — an entry dated later than now, which is what extrapolating from an
     earlier clock reading produces. c-log-timestamps-must-be-machine-read, which has had
     nowhere to run since 2026-09-08.
  3. YAML THAT JUST STOPPED PARSING — a write that leaves a checked YAML file unreadable. Added
     2026-09-12 on measured evidence: both broken files in Rite's first outside adoption were
     produced by in-session edits and committed before anything looked at them. INVALID only,
     never merely out-of-subset — see findings_for.

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
_SPEC: dict | None = None


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


def load_spec() -> dict:
    """The standard, or an empty mapping. Read once per process, not once per question."""
    global _SPEC
    if _SPEC is None:
        try:
            _SPEC = riteyaml.load(SPEC_PATH.read_text(encoding="utf-8"), str(SPEC_PATH)) or {}
        except (OSError, riteyaml.RiteYamlError):
            _SPEC = {}
    return _SPEC


def marker_of(root: Path) -> dict:
    """The project's .rite.yaml, or an empty mapping. An unreadable marker is the checker's
    finding to report, not the watcher's — here it simply means no declared scope."""
    try:
        return riteyaml.load((root / ".rite.yaml").read_text(encoding="utf-8"), ".rite.yaml") or {}
    except (OSError, riteyaml.RiteYamlError):
        return {}


def yaml_in_scope(root: Path, rel: str) -> bool:
    """Is this a YAML file the standard would grade?

    Scope is asked ONLY for a .yaml/.yml path, so the ordinary case — a write to a .py or .md
    file — costs one string test. Anything else would put a git call behind every edit in the
    session, and a watcher with a visible cost is a watcher that gets turned off.
    """
    if not rel.endswith((".yaml", ".yml")):
        return False
    spec = load_spec()
    if any(str(a.get("path")) == rel for a in spec.get("artifacts") or []):
        return True
    files, _ = riterules.project_yaml_files(root, spec, marker_of(root))
    return rel in set(files)


def findings_for(root: Path, rel: str) -> list[str]:
    notes: list[str] = []

    # ── YAML that just stopped being YAML ─────────────────────────────────────
    # MEASURED, and the reason this is at write time rather than only at session start: both
    # broken files in the first outside adoption were produced by in-session edits, and both were
    # committed before anything looked at them. The earliest honest moment to say so is now.
    #
    # INVALID ONLY, deliberately. An out-of-subset construct is a conformance note the checker
    # reports at leisure; saying it here would mean interrupting a write the project made on
    # purpose, which is how a watcher earns the reputation that gets it disabled.
    if yaml_in_scope(root, rel):
        verdict = riterules.yaml_verdict(root / rel, rel)
        if verdict is not None and verdict[0] == "invalid":
            _, construct, message = verdict
            notes.append(
                f"{rel} is no longer valid YAML — {construct}: {message}. The write that just "
                f"landed is where it broke, so this is the cheapest moment to fix it. Everything "
                f"that reads this file, Rite included, now knows nothing about its contents."
            )

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


# ── mid-session project switch ───────────────────────────────────────────────
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
            stamp.write_text(json.dumps(seen), encoding="utf-8", newline="\n")
        except OSError:
            pass
        return 0

    if first == str(root) or seen.get(session + ":reported"):
        return 0  # same project, or already said once

    try:
        seen[session + ":reported"] = True
        stamp.write_text(json.dumps(seen), encoding="utf-8", newline="\n")
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


def main() -> int:
    try:
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
            "additionalContext": "rite — on the file just written:\n  " + "\n  ".join(notes),
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
