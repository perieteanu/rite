#!/usr/bin/env python3
"""rite_paths — say whether this project participates, and where its documents actually are.

TWO FAILURES, ONE CAUSE, both measured on a real session in ~/projects/hwprivacy on 2026-09-12.

FIRST: every Rite tool returns 0 and prints nothing in a project with no .rite.yaml. /rite:end
is a Markdown prompt, so it runs anywhere — its step 6 ran `copy --all` and its step 7 ran
`check`, both reported success, and both had done nothing at all. The session's scratchpad was
rescued by hand. That is the skill's own preamble broken by the skill's own tools: "a skipped
step and a step with nothing to do must not look alike."

SECOND: the steps name docs/ROADMAP.yaml, docs/ARCHITECTURE.md, docs/DECISIONS.yaml and
docs/CONCERNS.yaml. hwprivacy has docs-yaml/, with YAML where the standard names Markdown and no
CONCERNS file at all. All four needed translating mid-ritual, and improvisation is where that
session corrupted a file — a hand-cut of the last list item took the section header with it, and
the result still PARSED.

So this prints both facts, and the skills inject its output before Claude reads them
(skills.md, Dynamic Context Injection). The agent is handed the real paths rather than asked to
remember that the named ones might be wrong.

IT READS AND PRINTS. It never writes, never creates a directory, and never exits non-zero for a
project that has not opted in — that is a fact to report, not an error.

Run:  python scripts/rite_paths.py [PROJECT_DIR]
Exit: 0 always
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import riterules  # noqa: E402
import riteyaml  # noqa: E402

ritefs.use_utf8_stdio()

SPEC_PATH = HERE.parent / "spec" / "project-standard.yaml"


def load(path: Path) -> dict:
    try:
        loaded = riteyaml.load(path.read_text(encoding="utf-8"), str(path))
    except (OSError, riteyaml.RiteYamlError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("-")]
    root = Path(args[0]).resolve() if args else Path.cwd()

    participating = ritefs.marker_present(root)
    marker = load(root / ritefs.MARKER) if participating else None
    spec = load(SPEC_PATH)
    if not spec:
        print(f"rite — cannot read the standard at {SPEC_PATH}.")
        print("  Paths cannot be resolved, so trust nothing below and resolve them by hand.")
        return 0

    legacy = marker.get("legacy_layout") if isinstance(marker, dict) else None
    legacy = legacy if isinstance(legacy, dict) else None
    dirs = riterules.docs_dirs(spec, marker)
    docs = dirs[0]

    print(f"rite — {root.name}")
    if not participating:
        # SAID FIRST AND SAID PLAINLY. Everything below is what the paths WOULD be, and a reader
        # who misses this line will believe the mechanical steps ran.
        print(f"  NOT PARTICIPATING — no {ritefs.MARKER} in this project.")
        print("  Rite's mechanical steps do nothing here and say nothing: `copy` and `check`")
        print("  both exit 0 having run no checks and copied no files. To preview without")
        print("  adopting, run `rite.sh check . --force`, which reads and never writes.")
        print()
    if legacy:
        by = legacy.get("migrate_by")
        when = f"migration due {by}" if by else "no migration date set"
        print(f"  legacy layout declared: {docs}/ ({when})")

    print("  documents, as they exist in THIS project:")
    rows: list[tuple[str, str]] = []
    for art in spec.get("artifacts") or []:
        rel = riterules.artifact_path(spec, str(art.get("id")), marker)
        if not rel:
            continue
        exists = ritefs.exists_exactly(root / rel)
        found = rel
        if not exists:
            # The artifact may be present under a superseded directory or extension, which is
            # precisely the case that cost the hwprivacy session four translations.
            stem, dot, ext = rel.partition(".")
            tail = stem.split("/", 1)[1] if "/" in stem else stem
            for d in dirs:
                for e in riterules.docs_formats(spec):
                    cand = f"{d}/{tail}.{e}"
                    if ritefs.exists_exactly(root / cand):
                        found, exists = cand, True
                        break
                if exists:
                    break
        if "<" in found or "*" in found:
            continue
        rows.append((found, "present" if exists else "ABSENT"))

    width = max((len(r) for r, _ in rows), default=0)
    for rel, state in sorted(rows):
        print(f"    {rel:<{width}}  {state}")
    absent = [r for r, s in rows if s == "ABSENT"]
    if absent:
        print(f"  {len(absent)} of {len(rows)} absent — do not edit a file that is not there;")
        print("  create it deliberately or record that the step had nothing to act on.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
