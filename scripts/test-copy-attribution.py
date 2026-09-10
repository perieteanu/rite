#!/usr/bin/env python3
"""Completion test: a plan is attributed by AUTHORSHIP, never by mention.

WHY THIS EXISTS, and it is not hypothetical. The first attributor written for rite_copy.py
searched every session transcript for the literal string "plans/<name>" and took the first
match. It mis-attributed FIVE of this machine's thirteen plans, handing rite half of
hwprivacy's work.

The cause is the part worth keeping: the contamination was SELF-INFLICTED. The session building
the tool ran `ls ~/.claude/plans/`, so rite's own transcript came to mention every plan on the
machine, and the naive index believed it. The act of measuring changed what was measured — and
the only reason it was caught is that the new numbers disagreed with a measurement taken twenty
minutes earlier. Nothing about the wrong answer looked wrong.

Authorship has exactly two shapes, and both name the file as a TOOL INPUT rather than as text:

  Write         input.file_path      == ~/.claude/plans/<name>.md
  ExitPlanMode  input.planFilePath   == ~/.claude/plans/<name>.md

A Bash command that lists the directory has neither, and must not attribute anything.

This test runs on SYNTHETIC transcripts in a temp directory. It never reads the real ones: a
test whose fixtures are the user's own session history would pass or fail for reasons that have
nothing to do with the code, and transcripts are private data this project has no business
reading for anything but a path.

Run:  python scripts/test-copy-attribution.py
Exit: 0 pass · 1 fail
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import rite_copy  # noqa: E402

ritefs.use_utf8_stdio()

PLAN = "cheeky-seeking-clock.md"
PLAN_PATH = f"/home/someone/.claude/plans/{PLAN}"


def line(tool: str, payload: dict) -> str:
    return json.dumps({
        "type": "assistant",
        "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": tool, "input": payload},
        ]},
    })


def text_line(body: str) -> str:
    return json.dumps({
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": body}]},
    })


CASES = [
    # (label, transcript lines, should_attribute)
    ("Write names the plan as file_path",
     [line("Write", {"file_path": PLAN_PATH, "content": "..."})], True),
    ("ExitPlanMode names it as planFilePath",
     [line("ExitPlanMode", {"plan": "...", "planFilePath": PLAN_PATH})], True),
    ("Bash merely lists the directory",
     [line("Bash", {"command": "ls ~/.claude/plans/", "description": "list plans"})], False),
    ("Bash output happens to contain the path",
     [line("Bash", {"command": f"cat {PLAN_PATH}", "description": "read it"})], False),
    ("prose mentions the path",
     [text_line(f"The plan is at {PLAN_PATH}, have a look.")], False),
    ("a Write to somewhere else entirely",
     [line("Write", {"file_path": "/home/someone/notes/" + PLAN, "content": "..."})], False),
    ("malformed json is skipped, not crashed on",
     ["{not json at all", line("Write", {"file_path": PLAN_PATH, "content": "..."})], True),
]


def main() -> int:
    failures: list[str] = []

    for label, lines, should in CASES:
        got: set[str] = set()
        for raw in lines:
            got |= rite_copy._authored_in(raw, {PLAN})
        did = PLAN in got
        if did != should:
            verb = "attributed" if did else "did not attribute"
            want = "should have" if should else "should not have"
            failures.append(f"{label}: {verb}, but {want}")

    # A conflict must be REPORTED as a conflict, never resolved by picking a winner.
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        projects = root / "projects"
        for slug in ("-a-project", "-b-project"):
            d = projects / slug
            d.mkdir(parents=True)
            (d / "s.jsonl").write_text(
                line("Write", {"file_path": PLAN_PATH, "content": "x"}) + "\n",
                encoding="utf-8", newline="\n")
        original = rite_copy.PROJECTS_DIR
        try:
            rite_copy.PROJECTS_DIR = projects
            index = rite_copy.build_attribution_index({PLAN})
        finally:
            rite_copy.PROJECTS_DIR = original
        owners = index.get(PLAN) or set()
        if owners != {"-a-project", "-b-project"}:
            failures.append(
                f"two sessions both wrote the plan; the index reported {sorted(owners)} "
                f"instead of both. Picking a winner quietly is the failure this project attacks."
            )

    if failures:
        print(f"FAIL  {len(failures)} attribution defect(s):")
        for f in failures:
            print(f"        {f}")
        return 1

    print(f"PASS  {len(CASES)} authorship case(s) distinguish writing from mentioning; "
          f"a two-session conflict is reported rather than resolved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
