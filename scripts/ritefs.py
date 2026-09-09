#!/usr/bin/env python3
"""ritefs — filesystem predicates that behave the same on every platform.

ONE implementation, several consumers. It exists because the same rule was written twice and
then not used a third time: rite-check.py carried a case-exact helper, while the checker's own
opt-in test and both hooks used Path.exists() anyway. A rule implemented in one file and
ignored in three is the failure this project is about.

See portability `case_sensitive_name_matching` in spec/project-standard.yaml.
"""

from __future__ import annotations

from pathlib import Path

MARKER = ".rite.yaml"


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
