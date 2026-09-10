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

if failures:
    print(f"FAIL  {len(failures)} defect(s) in the write-discipline watcher:")
    for f in failures:
        print(f"        {f}")
    sys.exit(1)

print(f"PASS  future timestamps are caught and past ones are not; the {len(paths)} append-only "
      f"artifacts are read from the spec, and MIXED files are not among them.")
sys.exit(0)
