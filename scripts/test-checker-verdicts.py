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
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()
CHECKER = HERE / "rite-check.py"

HEADER = '---\nschema_version: "1.0.0"\nas_of: "2026-09-09"\nstatus: current\n'
failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def run(root: pathlib.Path) -> str:
    out = subprocess.run([sys.executable, str(CHECKER), str(root), "--force"],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
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

# ── the declared claim surface ──────────────────────────────────────────────
# claims_match_filesystem was the last test parked in c-unimplementable-tests, and the reason
# was never difficulty: MISSION forbids inference at check time, and nothing in a document was
# machine-addressable. A `claims:` block on the provenance surface is the smallest thing that
# is. These cases are the four real failures of 2026-09-08/09 reduced to fixtures.

def claims_roadmap(block: str) -> str:
    """A ROADMAP carrying a claims block, otherwise minimal and valid."""
    return HEADER + block + "current_state: >\n  fine\n"


def verdicts(out: str, rule: str, path: str) -> list[str]:
    """The severity words of every finding for one rule on one artifact."""
    return [ln.split()[0] for ln in out.splitlines()
            if path in ln and rule in ln and ln.split()[:1]
            and ln.split()[0] in ("RED", "YELLOW", "GREEN", "NA")]


# 5. An `absent:` claim that has come TRUE is the api.pdf failure itself: the document says a
#    thing does not exist, and it does. RED, and it must NAME the path — a verdict that does
#    not say which claim broke sends the reader back to re-read the whole file.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp, claims_roadmap("claims:\n  absent:\n    - docs/ROADMAP.yaml\n"))
    out = run(tmp)
    v = verdicts(out, "claims_match_filesystem", "docs/ROADMAP.yaml")
    if v != ["RED"]:
        fail(f"an absent-claim that is false must be exactly one RED, got {v or 'nothing'}")
    if not any("docs/ROADMAP.yaml" in ln and "claims_match_filesystem" in ln
               for ln in out.splitlines()):
        fail("the claims verdict does not name the offending path")

# 6. A `present:` claim that has gone false — the opposite rot: a document listing files that
#    were later renamed or deleted.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp, claims_roadmap("claims:\n  present:\n    - scripts/nothing-here.py\n"))
    out = run(tmp)
    if verdicts(out, "claims_match_filesystem", "docs/ROADMAP.yaml") != ["RED"]:
        fail("a present-claim naming a missing file must be RED")

# 7. Claims that hold: GREEN, and a rule that fails everything would look strict while being
#    useless. GREEN findings are never PRINTED (rite-check.py suppresses them), so the
#    observable form of "it passed" is that the rule emits no line at all.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp, claims_roadmap(
        "claims:\n  absent:\n    - scripts/nothing-here.py\n  present:\n    - .rite.yaml\n"))
    out = run(tmp)
    v = verdicts(out, "claims_match_filesystem", "docs/ROADMAP.yaml")
    if v:
        fail(f"claims that all hold must pass silently (GREEN is not printed), got {v}")
    if "claims_declared" in out and verdicts(out, "claims_declared", "docs/ROADMAP.yaml"):
        fail("a document that declares claims must pass claims_declared silently")

# 8. No block at all: YELLOW from claims_declared (the nudge — this document asserts nothing
#    falsifiable), and NA from claims_match_filesystem (there is nothing to verify). Two
#    different questions, deliberately not collapsed into one verdict.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp, claims_roadmap(""))
    out = run(tmp)
    if verdicts(out, "claims_declared", "docs/ROADMAP.yaml") != ["YELLOW"]:
        fail("a document with no claims block must be YELLOW on claims_declared")
    if verdicts(out, "claims_match_filesystem", "docs/ROADMAP.yaml") != ["NA"]:
        fail("with no claims block there is nothing to verify — must be NA, not a pass")

# 9. A malformed block is RED, never ignored. A claim surface that silently does nothing is
#    precisely the defect this whole change exists to remove.
for name, block in {
    "not a mapping": "claims: nonsense\n",
    "value not a list": "claims:\n  absent: scripts/x.py\n",
    "unknown direction": "claims:\n  sometimes:\n    - scripts/x.py\n",
}.items():
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        scaffold(tmp, claims_roadmap(block))
        out = run(tmp)
        if verdicts(out, "claims_match_filesystem", "docs/ROADMAP.yaml") != ["RED"]:
            fail(f"a malformed claims block ({name}) must be RED, not ignored")

# 10. The case trap. macOS and Windows are case-insensitive, so a claim naming `.RITE.YAML`
#     would pass there and fail here — the same repo, two verdicts, which is the one outcome a
#     standard cannot tolerate. d-one-implementation-of-a-portability-rule.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp, claims_roadmap("claims:\n  present:\n    - .RITE.YAML\n"))
    out = run(tmp)
    if verdicts(out, "claims_match_filesystem", "docs/ROADMAP.yaml") != ["RED"]:
        fail("a present-claim differing only in case must fail on every platform")

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("PASS  unparseable is RED and named; absent stays NA; a broken marker is reported;\n"
      "      declared claims are checked against the tree and an undeclared one is nudged.")
sys.exit(0)
