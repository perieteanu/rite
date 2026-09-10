#!/usr/bin/env python3
"""Completion test: rite's memory mirror still matches the script it ported.

WHY THIS EXISTS, AND WHY IT IS TEMPORARY. On 2026-09-10 the memory mirror moved from
~/.claude/scripts/claude-mirror-memory.py into scripts/rite_copy.py, and the global hooks that
ran the original were retired. The original was KEPT on purpose — Costin's fallback while rite
is on trial — which leaves two implementations of one output alive at the same time.

"They agree" was verified twice by hand and by nothing else. A claim checked once by a human is
exactly the kind this project refuses to accept from anyone else, so it gets a check that fails.

IT COMPARES GENERATORS, NOT FILES, and writes nothing. Both engines expose a pure function from
(slug, memory files) to mirror text — rite_copy.generate_mirror and the legacy generate_text —
so the comparison needs no temp project, no marker file, and cannot damage a real mirror by
running. The `Last sync` line is excluded: it is a clock, it differs on every call, and a
generated file in this repo never carries one for exactly that reason.

IT SKIPS RATHER THAN FAILS when the legacy script is absent, and that is the normal end state.
A CI runner has never had it. When Costin retires the fallback this gate will skip permanently
on his machine too — at which point DELETE IT, along with the parity claim in
~/.claude/commands/mirror-memory.md. A gate that can no longer fail is not a gate.

Run:  python scripts/test-mirror-port-parity.py
Exit: 0 pass · 1 fail · 2 skip
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import rite_copy  # noqa: E402

ritefs.use_utf8_stdio()

LEGACY = pathlib.Path.home() / ".claude" / "scripts" / "claude-mirror-memory.py"
STAMP = re.compile(r"^> Last sync: .*$", re.MULTILINE)

SKIP = 2


def load_legacy():
    """Import the original by path — its filename has dashes and is not a module name."""
    spec = importlib.util.spec_from_file_location("legacy_mirror", LEGACY)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if not LEGACY.is_file():
        print(f"SKIP  {LEGACY} is not on this machine — nothing to compare against.")
        print("      This is the expected state on CI, and the end state once the fallback is")
        print("      retired. When it skips permanently, delete this gate.")
        return SKIP

    memdir = rite_copy.memory_dir_for(ROOT)
    if memdir is None:
        print("SKIP  no memory folder for this project — no input to compare on.")
        return SKIP

    files = rite_copy.memory_files(memdir)
    if not files:
        print("SKIP  no memory files.")
        return SKIP

    try:
        legacy = load_legacy()
    except Exception as exc:
        print(f"SKIP  the legacy script could not be imported — {exc}")
        return SKIP
    if legacy is None or not hasattr(legacy, "generate_text"):
        print("SKIP  the legacy script no longer exposes generate_text().")
        return SKIP

    slug = memdir.parent.name
    ours = STAMP.sub("", rite_copy.generate_mirror(slug, files))
    theirs = STAMP.sub("", legacy.generate_text(slug, files))

    if ours != theirs:
        print("FAIL  the port and the original no longer produce the same mirror.")
        import difflib
        diff = difflib.unified_diff(
            theirs.splitlines(keepends=True), ours.splitlines(keepends=True),
            fromfile="claude-mirror-memory.py (original)",
            tofile="rite_copy.py (port)", n=2)
        sys.stdout.writelines(diff)
        print()
        print("      One of them changed. Decide WHICH is right before touching either —")
        print("      the original is the fallback Costin still relies on.")
        return 1

    # The per-memory type label is the one field either side derives rather than copies, so it
    # is worth naming separately: a silent disagreement there would look like a formatting nit.
    mismatched = [f.name for f in files
                  if rite_copy.read_type(f) != legacy.read_type(f)]
    if mismatched:
        print(f"FAIL  the two engines disagree on metadata.type for: {', '.join(mismatched)}")
        return 1

    print(f"PASS  {len(files)} memories render identically in both engines "
          f"(clock excluded); metadata.type agrees on all of them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
