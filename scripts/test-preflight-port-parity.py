#!/usr/bin/env python3
"""Completion test: the ported session POST still agrees with the engine it came from.

WHY, AND WHY IT IS TEMPORARY. On 2026-09-10 preflight.py moved into Rite as
scripts/rite_preflight.py — d-preflight-is-config-not-fork. The original is KEPT as Costin's
fallback while Rite is on trial, so two implementations of one verdict are alive at once. The
same situation as the memory mirror, and it gets the same treatment: a gate, not a promise.

WHAT IT COMPARES: every check the port SHIPS must reach the same status and side as the
original, on this machine, right now. Three checks are deliberately absent from the port —
mirror_drift and last_log_age are superseded by Rite's own, and tracker_registered reads
project-tracker's files — so they are excluded by name rather than by a count, which would
silently pass if a fourth went missing.

IT SKIPS RATHER THAN FAILS when the original is absent, and that is the END STATE: a CI runner
never had it, and when Costin retires the fallback this skips forever. DELETE IT THEN — a gate
that can no longer fail is not a gate.

Run:  python scripts/test-preflight-port-parity.py
Exit: 0 pass · 1 fail · 2 skip
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import rite_preflight  # noqa: E402

ritefs.use_utf8_stdio()

LEGACY = pathlib.Path.home() / "projects" / "claude-preflight" / "preflight.py"

# Excluded BY NAME, never by count — see the docstring.
NOT_PORTED = {"mirror_drift", "last_log_age", "tracker_registered"}

SKIP = 2


def main() -> int:
    if not ritefs.exists_exactly(LEGACY):
        print(f"SKIP  {LEGACY} is not on this machine — nothing to compare against.")
        print("      Expected on CI, and the end state once the fallback is retired.")
        print("      When it skips permanently, delete this gate.")
        return SKIP

    spec = importlib.util.spec_from_file_location("legacy_preflight", LEGACY)
    if spec is None or spec.loader is None:
        print("SKIP  the original could not be loaded.")
        return SKIP
    legacy = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(legacy)
    except Exception as exc:
        print(f"SKIP  the original raised on import — {exc}")
        return SKIP

    cwd = ROOT
    try:
        theirs = {r.name: r for r in legacy.run_checks(
            legacy.Ctx(cwd, legacy.load_config()), False)}
        ours = {r.name: r for r in rite_preflight.run_checks(
            rite_preflight.Ctx(cwd, rite_preflight.load_config()), False)}
    except Exception as exc:
        print(f"SKIP  a check could not be run for comparison — {exc}")
        return SKIP

    failures: list[str] = []

    absent = NOT_PORTED & set(ours)
    if absent:
        failures.append(
            f"the port ships {', '.join(sorted(absent))}, which it must not. "
            f"mirror_drift and last_log_age are superseded by Rite's own checks; "
            f"tracker_registered reads project-tracker's files.")

    shared = (set(theirs) - NOT_PORTED) & set(ours)
    missing = set(theirs) - NOT_PORTED - set(ours)
    if missing:
        failures.append(f"the port dropped {', '.join(sorted(missing))} without a decision")

    for name in sorted(shared):
        a, b = theirs[name], ours[name]
        if a.status != b.status:
            failures.append(f"{name}: original says {a.status}, port says {b.status}")
        elif a.side != b.side:
            failures.append(f"{name}: original tags side {a.side}, port tags {b.side}")

    if failures:
        print(f"FAIL  {len(failures)} disagreement(s) between the port and the original:")
        for f in failures:
            print(f"        {f}")
        print()
        print("      Decide WHICH is right before touching either — the original is the")
        print("      fallback Costin still relies on.")
        return 1

    print(f"PASS  {len(shared)} shared check(s) agree on status and side; "
          f"the {len(NOT_PORTED)} unported checks are correctly absent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
