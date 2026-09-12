#!/usr/bin/env python3
"""Completion test: the write-discipline watcher speaks only when something is wrong.

TWO CONTRACTS, and the second is as load-bearing as the first.

  1. IT CATCHES what it exists to catch: an existing line changed in an append-only file, and a
     LOG entry dated in the future. Both are real failures of this project's own —
     a milestones entry once inserted mid-list, and ~30 entries extrapolated from a single
     22:11 clock reading, some AHEAD of real time.
  2. IT IS SILENT ON SUCCESS. It fires on every Write and Edit. A watcher that speaks when
     nothing is wrong is one the user disables within a day, and a disabled watcher catches
     nothing at all. Silence is not politeness here, it is the thing that keeps it installed.

The timestamp half runs on SYNTHETIC text, never on the repo's real LOG.md — a test whose
fixture is a live file passes or fails for reasons that have nothing to do with the code. The
first attempt at this used a hardcoded "19:20:00" as a supposedly-legal entry and it failed,
correctly, because the clock was 19:07. The check was right and the fixture was wrong; that is
exactly why fixtures are computed from `now` here.

Run:  python scripts/test-watch-discipline.py
Exit: 0 pass · 1 fail
"""

from __future__ import annotations

import datetime as dt
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import riterules  # noqa: E402
import rite_watch  # noqa: E402

ritefs.use_utf8_stdio()

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def entry(when: dt.datetime, text: str) -> str:
    dow = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][when.weekday()]
    return f"{when:%d-%m-%Y %H:%M:%S} | {dow} | rite | [note] {text}"


now = dt.datetime.now()

# ── the timestamp predicate ──────────────────────────────────────────────────
past = "\n".join([entry(now - dt.timedelta(hours=3), "earlier"),
                  entry(now - dt.timedelta(minutes=1), "just now")])
if riterules.log_future_timestamps(past, now):
    fail("flagged entries that are in the past — silence is the contract on success")

ahead = past + "\n" + entry(now + dt.timedelta(hours=2), "extrapolated, not read")
hits = riterules.log_future_timestamps(ahead, now)
if len(hits) != 1:
    fail(f"an entry two hours ahead produced {len(hits)} finding(s), expected 1")

# A minute of slack is deliberate: the entry is written before the file lands and clocks are not
# monotonic across a filesystem. A check that fires on a one-second skew gets switched off.
edge = past + "\n" + entry(now + dt.timedelta(seconds=30), "within tolerance")
if riterules.log_future_timestamps(edge, now):
    fail("fired inside the one-minute tolerance — that is the skew allowance, not a violation")

# Unparseable lines belong to entries_parse. Two rules reporting one defect is noise.
if riterules.log_future_timestamps("not a log line at all\n\n# heading", now):
    fail("reported something for text carrying no timestamps")

# ── what the watcher considers append-only ───────────────────────────────────
paths = rite_watch.append_only_paths()
if "LOG.md" not in paths:
    fail("LOG.md is not recognised as append-only — the spec declaration is not being read")
if "docs/DECISIONS.yaml" not in paths:
    fail("docs/DECISIONS.yaml is not recognised as append-only")
if any(p.endswith("ROADMAP.yaml") for p in paths):
    fail("ROADMAP.yaml was treated as append-only — it is MIXED, and deleting from its "
         "rewrite-only zone is required when closing an item, not a violation")

# ── the mid-session project switch ───────────────────────────────────────────
# CwdChanged has NO matcher support and fires on every directory change, so the discrimination
# is entirely in the code: a cd within one project must be silent, and only a move to a
# different project may speak. A watcher that flagged every cd would be disabled the same day.
import json  # noqa: E402
import tempfile  # noqa: E402

import rite_watch  # noqa: E402


def cwd_event(session: str, cwd: str, stamp: pathlib.Path) -> str:
    """Run the CwdChanged half against a temp stamp, returning whatever it printed."""
    import io
    import contextlib
    original = rite_watch.switch_stamp
    rite_watch.switch_stamp = lambda: stamp
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rite_watch.on_cwd_changed({"session_id": session, "hook_event_name": "CwdChanged",
                                       "cwd": cwd})
    finally:
        rite_watch.switch_stamp = original
    return buf.getvalue().strip()


with tempfile.TemporaryDirectory() as tmp:
    box = pathlib.Path(tmp)
    a, b = box / "project-a", box / "project-b"
    (a / "sub").mkdir(parents=True)
    b.mkdir()
    for d in (a, b):
        (d / ".rite.yaml").write_text("stage: idea\n", encoding="utf-8", newline="\n")
    stamp = box / "stamp.json"

    if cwd_event("s1", str(a), stamp):
        fail("spoke on the FIRST directory it saw — there is nothing to compare against yet")
    if cwd_event("s1", str(a / "sub"), stamp):
        fail("spoke on a cd WITHIN the same project — that is every other cd, and noise")

    spoke = cwd_event("s1", str(b), stamp)
    if not spoke:
        fail("stayed silent on a genuine move between two projects")
    else:
        try:
            ctx = json.loads(spoke)["hookSpecificOutput"]["additionalContext"]
        except (ValueError, KeyError):
            ctx = ""
            fail("the switch notice was not valid hookSpecificOutput JSON")
        if "project-a" not in ctx or "project-b" not in ctx:
            fail("the notice does not name both projects, so the reader cannot act on it")

    if cwd_event("s1", str(b), stamp):
        fail("spoke twice about the same switch — 'reported once' is what keeps it bearable")

    # A directory outside any Rite project is not ours to police.
    outside = box / "not-a-project"
    outside.mkdir()
    if cwd_event("s2", str(outside), stamp):
        fail("spoke about a directory carrying no .rite.yaml marker")

# ── YAML that just stopped parsing ───────────────────────────────────────────
# The third thing the watcher reports, added 2026-09-12. Both broken files in Rite's first outside
# adoption were produced by in-session edits and committed before anything looked at them, so the
# write itself is the earliest honest moment to speak.
#
# THE INVALID-ONLY CONTRACT IS TESTED HERE, not just documented: a file using an anchor is valid
# YAML the project wrote on purpose, and interrupting that write is how a watcher gets disabled.
with tempfile.TemporaryDirectory() as tmp:
    box = pathlib.Path(tmp)
    (box / "docs").mkdir()
    (box / ".rite.yaml").write_text("stage: idea\n", encoding="utf-8", newline="\n")

    def write(rel: str, body: str) -> list[str]:
        (box / rel).write_text(body, encoding="utf-8", newline="\n")
        return rite_watch.findings_for(box, rel)

    broke = write("docs/WORKLIST.yaml", "items:\n  - a: [unclosed\n")
    if len(broke) != 1:
        fail(f"a write that left a checked YAML file unreadable produced {len(broke)} note(s), "
             f"expected 1")
    elif "WORKLIST.yaml" not in broke[0] or "unterminated_flow" not in broke[0]:
        fail(f"the note names neither the file nor the construct: {broke[0][:90]}")

    if write("docs/FAULTS.yaml", "faults:\n  - id: one\n"):
        fail("spoke about a well-formed YAML file — silence on success is the contract")

    if write("docs/PARTS.yaml", "base: &defaults\n  a: 1\n"):
        fail("spoke about an anchor: valid YAML outside the subset is the checker's conformance "
             "note, not an interruption at the moment of writing")

    if write("scratch.yaml", "a: [unclosed\n"):
        fail("graded a YAML file outside the checked scope — the default scope is the "
             "documentation directory, and reaching beyond it is the project's call to declare")

if failures:
    print(f"FAIL  {len(failures)} defect(s) in the write-discipline watcher:")
    for f in failures:
        print(f"        {f}")
    sys.exit(1)

print(f"PASS  future timestamps are caught and past ones are not; the {len(paths)} append-only "
      f"artifacts are read from the spec, MIXED files are not among them, and a project\n"
      f"      switch is reported once while every cd within a project is silent.")
sys.exit(0)
