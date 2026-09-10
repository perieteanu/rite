#!/usr/bin/env python3
"""ritefs — filesystem predicates that behave the same on every platform.

ONE implementation, several consumers. It exists because the same rule was written twice and
then not used a third time: rite-check.py carried a case-exact helper, while the checker's own
opt-in test and both hooks used Path.exists() anyway. A rule implemented in one file and
ignored in three is the failure this project is about.

See portability `case_sensitive_name_matching` in spec/project-standard.yaml.
"""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = ".rite.yaml"


def use_utf8_stdio() -> None:
    """Declare this process's stdout and stderr as UTF-8. Call it first, in every entry point.

    See portability `process_output_declares_encoding` in spec/project-standard.yaml.

    Python picks the console codepage on Windows, so a report containing `·` or `—` is written
    as cp1252 there and as UTF-8 on Linux and macOS — the same program, three byte streams.
    Found on 2026-09-10 by the first CI run that was not on Linux: run-gates.py captured a
    child's output with encoding="utf-8", the child had emitted cp1252, and a reader thread
    died with `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97` — 0x97 being cp1252's
    em dash. Two gates reported FAIL for a reason that had nothing to do with what they test.

    The worse failure is quieter and was found while fixing that one. A parent that decodes a
    child with the locale encoding and then searches for a literal like "checks ·" matches by
    coincidence on cp1252 and silently fails to match on cp437 or cp850, losing the line
    instead of erroring. Both halves — how output is written and how it is read — have to name
    the encoding, or a byte means different things at each end of one pipe.

    Not ASCII-only instead: the messages come from YAML that is full of em dashes, so the
    encoding must be stated rather than avoided.

    Silent when stdout has been replaced by something without reconfigure(), which is normal
    under test harnesses and in embedded interpreters.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                # A detached or already-closed stream. Losing the declaration is survivable;
                # taking the process down over it is not.
                pass


def exists_exactly(path: Path) -> bool:
    """Case-SENSITIVE presence test for one path.

    Never Path.exists(): macOS and Windows are case-insensitive, so `readme.md` passes there
    and fails on Linux — the same repo, two verdicts, which is the one outcome a standard
    cannot tolerate. Listing the parent and comparing names is the portable way to ask.
    """
    parent = path.parent
    if not parent.is_dir():
        return False
    return path.name in {c.name for c in parent.iterdir()}


def marker_present(root: Path) -> bool:
    """Has this project opted in? Presence of the marker IS the signal; contents are optional.

    Spelled exactly, for the reason above: a project carrying `.Rite.yaml` must not opt in on
    a Mac and vanish on Linux.
    """
    return exists_exactly(root / MARKER)
