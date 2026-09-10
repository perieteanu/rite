#!/usr/bin/env python3
"""rite_issue — record something Rite got wrong, from wherever you hit it.

THE GAP THIS CLOSES, and it was found by the user asking the obvious question: Rite has
CONCERNS.yaml, and CONCERNS.yaml belongs to the project you are IN. When Rite annoys you inside
somebody else's project — a car log, a scraper, a recipe folder — that concern belongs to RITE,
and there was no path from one to the other. You were relying on remembering it, which is the
one thing this project exists to distrust.

WHY IT WRITES SOMEWHERE ELSE, not into the current project: the note is not about that project
and does not belong in its record. It goes to ${CLAUDE_PLUGIN_DATA}/feedback.md — plugin
storage, the same declared exception the config and the dedup stamp already use. Not an
artifact, so the inventory stays at 14.

IT IS DELIBERATELY DUMB. It appends a timestamped line and nothing else: no triage, no
severity, no id. Those are judgements, and judgements made at the moment of annoyance are worse
than judgements made later with the whole list in front of you. Harvesting into CONCERNS.yaml
is a separate, deliberate act.

APPEND-ONLY, and it never rewrites. The file is the raw record of what irritated a user in the
moment, which is exactly the thing that gets tidied into uselessness.

Run:  rite.sh issue "the report says NA nine times and I stopped reading it"
      rite.sh issue --list
Exit: 0 on success, 2 on a usage error.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

USAGE = """rite issue — record something Rite got wrong.

Usage:
  rite.sh issue "<what happened>"     append a note, from any project
  rite.sh issue --list                show what has been recorded
  rite.sh issue --path                print the file's location

The note lands in ${CLAUDE_PLUGIN_DATA}/feedback.md, NOT in the project you are in — it is
about Rite, not about your work. Harvest it into rite's CONCERNS.yaml when you are ready.
"""


def feedback_path() -> Path:
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    return Path(base or (Path.home() / ".claude" / "rite")) / "feedback.md"


def project_label(cwd: Path) -> str:
    """The marked project this note came from, or the bare directory name.

    Named rather than pathed, because the useful question when harvesting is "which KIND of
    project was this?" — a scraper, a recipe folder — not where it sat on disk.
    """
    for candidate in [cwd, *cwd.parents]:
        if ritefs.marker_present(candidate):
            return candidate.name
    return cwd.name


def append(text: str) -> int:
    path = feedback_path()
    now = dt.datetime.now()
    cwd = Path.cwd().resolve()
    entry = (f"\n## {now:%Y-%m-%d %H:%M:%S} · {project_label(cwd)}\n"
             f"<!-- cwd: {cwd} -->\n\n{text.strip()}\n")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        new = not ritefs.exists_exactly(path)
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            if new:
                fh.write("# Rite — what it got wrong\n\n"
                         "Append-only. Raw notes from the moment of annoyance, deliberately\n"
                         "untriaged: a judgement made while irritated is worse than one made\n"
                         "later with the whole list in view. Harvest into rite's CONCERNS.yaml.\n")
            fh.write(entry)
    except OSError as exc:
        print(f"rite: could not write {path} — {exc}", file=sys.stderr)
        return 2
    print(f"recorded in {path}")
    return 0


def show() -> int:
    path = feedback_path()
    if not ritefs.exists_exactly(path):
        print(f"nothing recorded yet ({path})")
        return 0
    print(path.read_text(encoding="utf-8", errors="replace").rstrip())
    return 0


def main(argv: list[str]) -> int:
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(USAGE, end="")
        return 0 if args else 2
    if args[0] == "--list":
        return show()
    if args[0] == "--path":
        print(feedback_path())
        return 0
    if args[0].startswith("-"):
        print(f"rite issue: unknown option: {args[0]}", file=sys.stderr)
        print("            run with --help for usage.", file=sys.stderr)
        return 2
    text = " ".join(args).strip()
    if not text:
        print("rite issue: nothing to record.", file=sys.stderr)
        return 2
    return append(text)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
