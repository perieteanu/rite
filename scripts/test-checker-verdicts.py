#!/usr/bin/env python3
"""Contract test: the checker must not hide its own failures behind a benign verdict.

Closes the regression half of c-na-conflates-absent-with-unparseable. Until 2026-09-09 a file
Rite could not PARSE and a file the project never WROTE both reported
`NA — file absent or unparseable`. NA reads as nothing-to-see, so the checker stayed calm while
knowing nothing: on that day it buried four real parser refusals across two projects, nine NA
lines deep, and made a written prediction untestable.

The distinction under test is therefore not cosmetic. ABSENT is a fact about the project.
UNPARSEABLE is a fact about Rite, and it must be loud.

Run:  python scripts/test-checker-verdicts.py
Exit: 0 pass · 1 fail
"""

from __future__ import annotations

import pathlib
import re
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

# ── stage as the gating axis ────────────────────────────────────────────────
# Measured on 2026-09-10: an empty project declaring `stage: idea` scored 9 RED and 0 GREEN,
# because stage gated one artifact and tier gated the rest. A tool that opens by listing
# everything you have not done yet is uninstalled the next day — d-stage-gates-the-standard.


def reds_for(out: str) -> list[str]:
    return [ln.strip() for ln in out.splitlines() if ln.strip().startswith("RED")]


def bare_project(tmp: pathlib.Path, marker: str) -> str:
    """A project carrying nothing but the marker."""
    (tmp / ".rite.yaml").write_text(marker, encoding="utf-8", newline="\n")
    return run(tmp)


# 11. At `idea` a project is asked for LOG and HANDOFF, and for nothing else.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    out = bare_project(tmp, "stage: idea\n")
    reds = reds_for(out)
    if len(reds) != 2:
        fail(f"stage idea must require exactly 2 artifacts, got {len(reds)}: "
             f"{[r[:60] for r in reds]}")
    if not (any("LOG.md" in r for r in reds) and any("HANDOFF.md" in r for r in reds)):
        fail(f"stage idea must require LOG.md and HANDOFF.md; got {[r[:60] for r in reds]}")

# 12. THE ANTI-LOOPHOLE CASE, and the one that matters most. A marker with no stage must keep
#     the OLD tier-based behaviour. If absence meant "require nothing", deleting one line from
#     .rite.yaml would switch the standard off.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    out = bare_project(tmp, "# no stage declared\n")
    reds = reds_for(out)
    if len(reds) != 9:
        fail(f"a marker with NO stage must still require all of tier 0+1 (9 artifacts), "
             f"got {len(reds)} — absence must never be a way to silence the standard")

# 13. A not-yet-due artifact is NA and says WHY. It must not look like one that passed, and
#     must not look like one that failed.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    out = bare_project(tmp, "stage: idea\n")
    # Its individual lines are COLLAPSED into the summary (case 17), so what must hold is that
    # it is never RED and is still named under the stage that will require it.
    if any("docs/ARCHITECTURE.md" in ln and ln.strip().startswith(("RED", "YELLOW"))
           for ln in out.splitlines()):
        fail("an artifact below its required stage must never be RED or YELLOW")
    build_line = [ln for ln in out.splitlines()
                  if ln.strip().startswith("build") and "docs/ARCHITECTURE.md" in ln]
    if not build_line:
        fail("a stage-deferred artifact must be listed under the stage that would require it")

# 14. A DECLARATION BEATS TIER. LICENSE is tier 2 and required from `shipped`; an earlier gate
#     let `tier >= 2` short-circuit the stage, so it stayed optional at every stage and a
#     project could publish with no licence — the exact failure the field exists to prevent.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    out = bare_project(tmp, "stage: shipped\n")
    lic = [ln for ln in out.splitlines() if "LICENSE" in ln and "file_present" in ln]
    if not lic or not lic[0].strip().startswith("RED"):
        fail("LICENSE must be RED at stage shipped — tier must not override a declared stage")

# 15. Ruling A: a declared standard_version that does not match is YELLOW, and names both.
#     Never RED: Rite keeps no old rule sets, so it cannot honour a pin.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    out = bare_project(tmp, "stage: idea\nstandard_version: \"0.0.1\"\n")
    sv = [ln.strip() for ln in out.splitlines() if "standard_version" in ln]
    if not sv or not sv[0].startswith("YELLOW"):
        fail("a standard_version mismatch must be YELLOW, never RED and never silent")
    elif "0.0.1" not in sv[0]:
        fail("the standard_version finding must name the version the project targets")

# 16. ...and a project that declares no standard_version is silent about it. The common case
#     must not be nagged.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    out = bare_project(tmp, "stage: idea\n")
    if any("standard_version" in ln for ln in out.splitlines()):
        fail("a project declaring no standard_version must not be told anything about it")

# 17. STAGE-DEFERRED CHECKS ARE COLLAPSED BUT NOT DROPPED. Measured on 2026-09-10: a project at
#     stage `idea` printed 54 lines to convey ONE finding, 46 of them "not required before
#     stage X". Collapsing is only safe while the count stays honest and the artifacts stay
#     named — otherwise it is hiding, and this project's rule is that a check which vanished
#     and one that passed must never look alike.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    out = bare_project(tmp, "stage: idea\n")

    printed = [ln for ln in out.splitlines() if ln.startswith("  ")]
    if len(printed) > 25:
        fail(f"a stage-idea project printed {len(printed)} lines — the stage-deferred checks "
             f"are not being collapsed")

    summary = [ln for ln in out.splitlines() if "not required at stage" in ln]
    if not summary:
        fail("the collapsed summary line is missing entirely")
    else:
        # A COUNT, NOT A LITERAL — the same lesson as the NA assertion below. This pinned "46"
        # and broke the moment a test was declared on a build-stage artifact, which is noise
        # rather than a finding. The claim is that the collapsed line SAYS HOW MANY it stands
        # for, so a reader can see what is coming; the exact number is not the contract.
        stands_for = re.search(r"(\d+)\s+checks not required", summary[0])
        if not stands_for:
            fail(f"the collapsed line must state HOW MANY checks it stands for: {summary[0].strip()}")
        elif int(stands_for.group(1)) < 1:
            fail(f"the collapsed line claims to stand for nothing: {summary[0].strip()}")

    # The artifacts must still be named, or the user cannot learn what is coming.
    for want in ("README.md", "docs/MISSION.md", "docs/ARCHITECTURE.md", "LICENSE"):
        if want not in out:
            fail(f"a stage-deferred artifact vanished from the report entirely: {want}")

    # And the totals must be untouched: collapsing is a display choice, never a verdict change.
    #
    # ASSERTED AS AN INVARIANT, NOT A LITERAL. This line pinned "59 NA", then "60 NA", and was
    # about to pin "61 NA" — it broke three times in one day, every time an artifact or a rule
    # was added, and each break was noise rather than a finding. The number was never the point:
    # the claim is that every declared check lands in exactly one bucket, so collapsing cannot
    # quietly drop one. That holds whatever the counts are.
    total = [ln for ln in out.splitlines() if "checks ·" in ln]
    if not total:
        fail("the summary line is missing entirely")
    else:
        nums = [int(x) for x in re.findall(r"(\d+)\s+(?:checks|RED|YELLOW|NA|GREEN)", total[0])]
        if len(nums) != 5:
            fail(f"could not read the five counts from: {total[0].strip()}")
        elif nums[0] != sum(nums[1:]):
            fail(f"collapsing lost a check — {nums[0]} declared but "
                 f"{sum(nums[1:])} accounted for: {total[0].strip()}")

# ── the CLI contract ─────────────────────────────────────────────────────────
# Until 2026-09-10 every unrecognised flag was silently discarded: `--help` ran a full check,
# and a typo'd `--exclude-scpoe=session` scored at FULL strength while the caller believed a
# scope had been excluded. A flag that looks accepted and does nothing is a silent wrong
# answer — the failure class this project attacks, in its own entry point. These cases exist
# so it cannot come back.
def cli(*argv: str) -> tuple[int, str, str]:
    out = subprocess.run([sys.executable, str(CHECKER), *argv],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return out.returncode, out.stdout, out.stderr


code, out, _ = cli("--help")
if code != 0:
    fail(f"--help exited {code}, expected 0")
if "Usage:" not in out or "--exclude-scope=SCOPE" not in out:
    fail("--help printed no usage naming the real flags")
if "checks ·" in out:
    fail("--help RAN A CHECK instead of printing usage — the original defect")

code, _, err = cli("--exclude-scpoe=session")
if code != 2:
    fail(f"a typo'd flag exited {code}, expected 2 — it must not be silently ignored")
if "--exclude-scpoe=session" not in err:
    fail("the unknown flag was rejected without naming it")

code, _, err = cli("--exclude-scope", "session")
if code != 2:
    fail(f"the separate form exited {code}, expected 2 — a bare value reads as PROJECT_DIR")
if "with an '='" not in err:
    fail("the separate form was rejected without suggesting the joined one")

code, out, _ = cli(str(HERE.parent), "--force", "--exclude-scope=session")
if code not in (0, 1):
    fail(f"a fully valid invocation exited {code}")
if "checks ·" not in out:
    fail("a valid invocation did not run a check")

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("PASS  unparseable is RED and named; absent stays NA; a broken marker is reported;\n"
      "      declared claims are checked against the tree and an undeclared one is nudged;\n"
      "      stage gates what is required, a declaration beats tier, and no stage means no\n"
      "      leniency; unknown flags are rejected rather than swallowed.")
sys.exit(0)
