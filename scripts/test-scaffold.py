#!/usr/bin/env python3
"""Completion test for the seed set: a scaffolded project must open on GREEN.

ROADMAP required each seed file to be "the VALID SMALLEST INSTANCE: it has to pass rite-check".
That claim could not be checked where it was written. template/LOG.md is not at a canonical
path, so the checker never looks at it — the templates could drift arbitrarily far from the
standard and nothing would notice. The check that means something is this one:

    scaffold into a temp directory, run the checker against the RESULT, require 0 RED.

It also caught a real defect on the day it was written: the first template/LOG.md carried a
prose preamble explaining the log format, and entries_parse counted those nine lines as broken
entries. Every project scaffolded by Rite would have opened on a YELLOW produced by Rite's own
seed file. Guidance prose also has no business in an append-only file, where it becomes a
permanent header nobody can tidy later.

Run:  python scripts/test-scaffold.py
Exit: 0 pass · 1 fail
"""

from __future__ import annotations

import datetime as dt
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

INIT = HERE / "rite_init.py"
CHECKER = HERE / "rite-check.py"

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def run(script: pathlib.Path, *args: str) -> str:
    out = subprocess.run([sys.executable, str(script), *args],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return out.stdout + out.stderr


def scaffold(tmp: pathlib.Path) -> str:
    return run(INIT, str(tmp))


def check(tmp: pathlib.Path) -> str:
    return run(CHECKER, str(tmp))


def counts(report: str) -> tuple[int, int]:
    """(RED, YELLOW) from the checker's summary line."""
    for ln in report.splitlines():
        if "checks ·" in ln:
            parts = ln.split("·")
            return int(parts[1].split()[0]), int(parts[2].split()[0])
    return -1, -1


# 1. THE HEADLINE CLAIM. A project scaffolded from nothing opens with no findings at all.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp)
    red, yellow = counts(check(tmp))
    if red != 0:
        fail(f"a freshly scaffolded project must have 0 RED, got {red}")
    if yellow != 0:
        fail(f"a freshly scaffolded project must have 0 YELLOW, got {yellow} — a seed file "
             f"that trips the standard is worse than no seed file")

# 2. Every token is substituted. A literal {{ reaching a user's project means a template gained
#    a placeholder the scaffolder does not know about.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp)
    for name in (ritefs.MARKER, "LOG.md", "HANDOFF.md"):
        body = (tmp / name).read_text(encoding="utf-8")
        if "{{" in body or "}}" in body:
            fail(f"{name} still contains an unsubstituted token")

# 3. The dates are REAL and read at scaffold time. A baked date would start the 30-day
#    freshness clock on the day the template was committed.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp)
    today = dt.date.today()
    log = (tmp / "LOG.md").read_text(encoding="utf-8")
    if today.strftime("%d-%m-%Y") not in log:
        fail("the seeded LOG entry does not carry today's date")
    handoff = (tmp / "HANDOFF.md").read_text(encoding="utf-8")
    if f'written: "{today.isoformat()}"' not in handoff:
        fail("the seeded HANDOFF is not dated today")
    if f'expires: "{today.isoformat()}"' in handoff:
        fail("the seeded HANDOFF expires the day it is written")

# 4. NEVER OVERWRITES, and the second run says so rather than going quiet.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp)
    (tmp / "LOG.md").write_text("# mine\n", encoding="utf-8", newline="\n")
    out = scaffold(tmp)
    if (tmp / "LOG.md").read_text(encoding="utf-8") != "# mine\n":
        fail("a second run overwrote an existing file — the seed must never clobber work")
    if "skipped" not in out:
        fail("a second run must report what it skipped, not pass over it in silence")

# 5. HONEST ABOUT WHAT IT WILL NOT WRITE. Raising the stage must produce findings naming the
#    documents a human has to write — the scaffolder deliberately seeds none of them.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp)
    (tmp / ritefs.MARKER).write_text("stage: spec\n", encoding="utf-8", newline="\n")
    report = check(tmp)
    red, _ = counts(report)
    if red != 4:
        fail(f"at stage spec a scaffolded project must be asked for 4 more documents, got {red}")
    for want in ("README.md", "CLAUDE.md", "MISSION", "ROADMAP"):
        if want not in report:
            fail(f"the stage-spec report does not name {want}")

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("PASS  a scaffolded project opens 0 RED / 0 YELLOW; tokens are substituted, dates are\n"
      "      read at scaffold time, existing files are never overwritten, and raising the\n"
      "      stage names the documents the scaffolder will not write.")
sys.exit(0)
