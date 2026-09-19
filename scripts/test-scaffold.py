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

Run:  <python> scripts/test-scaffold.py
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
import rite_init  # noqa: E402
import ritefs  # noqa: E402
import riterules  # noqa: E402

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
    for name in (ritefs.MARKER, "LOG.md", "HANDOFF.md", ".gitignore"):
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
    if f'closed: "{today.isoformat()}"' not in handoff:
        fail("the seeded HANDOFF carries no close record dated today")
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

# 6. THE SEEDED .gitignore COVERS EVERY ARTIFACT RITE COPIES OUT OF ~/.claude, and covers them
#    FUNCTIONALLY — the rules are checked with `git check-ignore` against real paths rather than
#    compared as strings, because a pattern that reads right and matches nothing fails silently
#    in the direction that publishes. This is the gate on d-agent-copies-default-untracked: the
#    ignore rules are derived from the standard, so declaring a fourth copied artifact without
#    covering it here fails rather than shipping a hole.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    scaffold(tmp)
    body = (tmp / ".gitignore").read_text(encoding="utf-8")
    spec = riterules.load_spec(HERE.parent / "spec" / "project-standard.yaml")
    for artifact_id in rite_init.AGENT_COPY_ARTIFACTS:
        declared = riterules.artifact_path(spec, artifact_id)
        if not declared:
            fail(f"the standard declares no path for {artifact_id}, so the seed cannot cover it")
            continue
        if riterules.ignore_pattern(declared) not in body.splitlines():
            fail(f"the seeded .gitignore does not ignore {artifact_id} ({declared})")

    # The functional half. git is a capability, not a prerequisite — say so rather than pass.
    git = subprocess.run(["git", "-C", str(tmp), "init", "-q"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if git.returncode != 0:
        print("SKIP  no git — the ignore rules were compared as text, never exercised")
    else:
        today = dt.date.today().isoformat()
        samples = {
            "docs/claude-memory.md": True,
            f"docs/PLAN-{today}-some-slug.md": True,
            f"docs/session-scripts/{today}/fix_thing.py": True,
            # Must NOT be ignored: the user's own documents are theirs to publish.
            "docs/DECISIONS.yaml": False,
            "LOG.md": False,
        }
        for rel, want_ignored in samples.items():
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x\n", encoding="utf-8", newline="\n")
            r = subprocess.run(["git", "-C", str(tmp), "check-ignore", "-q", rel],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            ignored = r.returncode == 0
            if ignored != want_ignored:
                verb = "must be ignored" if want_ignored else "must NOT be ignored"
                fail(f"{rel} {verb} by the seeded .gitignore")

# 7. AN EXISTING .gitignore IS NEVER EDITED — the paths are printed for the user to paste or
#    refuse. Rite writing into a file it did not create is the behaviour this whole default
#    exists to avoid making automatic.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    mine = "node_modules/\n"
    (tmp / ".gitignore").write_text(mine, encoding="utf-8", newline="\n")
    out = scaffold(tmp)
    if (tmp / ".gitignore").read_text(encoding="utf-8") != mine:
        fail("an existing .gitignore was modified — it must be left byte-identical")
    if "docs/claude-memory.md" not in out:
        fail("with a .gitignore already present, the copied paths must be printed for the user")

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("PASS  a scaffolded project opens 0 RED / 0 YELLOW; tokens are substituted, dates are\n"
      "      read at scaffold time, existing files are never overwritten, the seeded .gitignore\n"
      "      really ignores every artifact Rite copies out of ~/.claude and nothing the user\n"
      "      wrote, and raising the stage names the documents the scaffolder will not write.")
sys.exit(0)
