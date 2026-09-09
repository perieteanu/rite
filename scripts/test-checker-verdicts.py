#!/usr/bin/env python3
"""Contract test: the checker must not hide its own failures behind a benign verdict.

Closes the regression half of c-na-conflates-absent-with-unparseable. Until 2026-09-09 a file
Rite could not PARSE and a file the project never WROTE both reported
`NA — file absent or unparseable`. NA reads as nothing-to-see, so the checker stayed calm while
knowing nothing: on that day it buried four real parser refusals across two projects, nine NA
lines deep, and made a written prediction untestable.

The distinction under test is therefore not cosmetic. ABSENT is a fact about the project.
UNPARSEABLE is a fact about Rite, and it must be loud.

Run:  python3 scripts/test-checker-verdicts.py
Exit: 0 pass · 1 fail
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CHECKER = HERE / "rite-check.py"

HEADER = '---\nschema_version: "1.0.0"\nas_of: "2026-09-09"\nstatus: current\n'
failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def run(root: pathlib.Path) -> str:
    out = subprocess.run([sys.executable, str(CHECKER), str(root), "--force"],
                         capture_output=True, text=True, encoding="utf-8")
    return out.stdout + out.stderr


def scaffold(tmp: pathlib.Path, roadmap: str, marker: str = "# marker\n") -> None:
    (tmp / "docs").mkdir(parents=True, exist_ok=True)
    (tmp / ".rite.yaml").write_text(marker, encoding="utf-8", newline="\n")
    (tmp / "docs" / "ROADMAP.yaml").write_text(roadmap, encoding="utf-8", newline="\n")


# 1. Present but unparseable: exactly one RED naming the construct, and no pretence that the
#    remaining checks ran.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp, HEADER + "base: &defaults\n  a: 1\n")
    out = run(tmp)
    road = [ln for ln in out.splitlines() if "docs/ROADMAP.yaml" in ln]
    reds = [ln for ln in road if ln.strip().startswith("RED")]
    if len(reds) != 1:
        fail(f"expected exactly 1 RED for an unparseable ROADMAP, got {len(reds)}")
    elif "anchors" not in reds[0]:
        fail(f"the RED does not name the offending construct: {reds[0].strip()}")
    if any("absent" in ln for ln in road):
        fail("an unparseable file was still described as 'absent' somewhere")
    if not any("checks_not_run" in ln for ln in road):
        fail("the skipped checks were not accounted for — they must be stated, not vanish")

# 2. Parseable: no parse RED at all. Guards against the fix firing on healthy files.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp, HEADER + "current_state: >\n  fine\n")
    out = run(tmp)
    if any("parseable" in ln and ln.strip().startswith("RED") for ln in out.splitlines()):
        fail("a well-formed ROADMAP was reported as unparseable")

# 3. Absent optional artifact stays NA. ABSENT must NOT be swept up by the new RED.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp, HEADER + "current_state: >\n  fine\n")
    out = run(tmp)
    lic = [ln for ln in out.splitlines() if "LICENSE" in ln]
    if lic and any(ln.strip().startswith("RED") and "parseable" in ln for ln in lic):
        fail("an absent optional artifact was reported as a parse failure")

# 4. An unreadable marker must be reported, never silently replaced by defaults.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp, HEADER + "current_state: >\n  fine\n", marker="thresholds: {\n")
    out = run(tmp)
    if ".rite.yaml" not in out or "unparseable" not in out:
        fail("an unparseable .rite.yaml was accepted in silence — its overrides were dropped "
             "without a word")

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("PASS  unparseable is RED and named; absent stays NA; a broken marker is reported.")
sys.exit(0)
