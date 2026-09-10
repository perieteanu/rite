#!/usr/bin/env python3
"""rite_init — seed a project so it opens on GREEN at stage `idea`.

WHAT IT WRITES, AND WHY IT REFUSES TO WRITE MORE. Three files: .rite.yaml, LOG.md, HANDOFF.md.
That is exactly what stage `idea` requires, and `idea` is the only stage whose requirements a
machine can satisfy HONESTLY:

  - a LOG carrying one real entry IS a complete log
  - a HANDOFF with `genre: none` IS a complete handoff — the standard says so outright: a real
    answer, the assertion that none is needed, made by someone who considered the question

Nothing else qualifies. A seeded MISSION.md that nobody has written is a lie that passes
file_present, and the `populated` tests cannot tell a filled template from an unfilled one —
give it enough headings and it scores. Seeding prose would manufacture precisely the
confidently-wrong document this project exists to attack, and would do it at first contact.
So advancing past `idea` stays a human act, and the checker names exactly which files it wants.

NEVER OVERWRITES. An existing file is left alone and reported as skipped, so the command is safe
to re-run and re-running is the intended use. It does not touch ~/.claude, install anything, or
run git — see d-never-instruct-installation.

Run:  python scripts/rite_init.py [PROJECT_DIR] [--name SHORT_NAME]
Exit: 0 wrote or skipped cleanly · 1 the project directory is unusable
"""

from __future__ import annotations

import datetime as dt
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

TEMPLATE = ROOT / "template"

# Which template file lands where. The marker's name comes from ritefs so there is one spelling
# of it in the codebase rather than three.
SEEDS = {
    ".rite.yaml": ritefs.MARKER,
    "LOG.md": "LOG.md",
    "HANDOFF.md": "HANDOFF.md",
}

# How long a seeded handoff stays live. A `genre: none` handoff describes a project nobody has
# worked in yet, so it has nothing to go stale ABOUT — but `expires` must be a real date, and an
# unbounded one would be a promise rather than a date. 90 days matches what this project's own
# handoffs have used.
HANDOFF_LIFETIME_DAYS = 90

# Day abbreviations are written out rather than taken from strftime("%a"), which is LOCALE
# DEPENDENT: on this machine the system locale is ro_RO and %a yields "Jo" for Thursday. The
# LOG format declares English abbreviations for parser stability, so the mapping is explicit.
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def short_name_for(root: pathlib.Path) -> str:
    """A parser-safe short name derived from the directory, since LOG lines are pipe-delimited."""
    raw = root.resolve().name or "project"
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-")
    return cleaned or "project"


def substitutions(short_name: str) -> dict[str, str]:
    """Read the clock ONCE, here, and derive every token from it.

    The usual rule is that generated output must never carry a timestamp — a clock in a
    generated file makes its drift gate fail on every run. Scaffolded output is the exact
    inversion: these dates MUST be real, because newest_entry_within_days_of_activity and
    not_expired both read them. A template with a baked date starts a 30-day clock the day it is
    committed and ships already stale, so the date is read at scaffold time, never authored in.
    """
    now = dt.datetime.now()
    return {
        "{{DATE}}": now.strftime("%d-%m-%Y"),
        "{{DATE_ISO}}": now.strftime("%Y-%m-%d"),
        "{{TIME}}": now.strftime("%H:%M:%S"),
        "{{DOW}}": DOW[now.weekday()],
        "{{EXPIRES}}": (now.date() + dt.timedelta(days=HANDOFF_LIFETIME_DAYS)).isoformat(),
        "{{SHORT_NAME}}": short_name,
    }


def render(text: str, subs: dict[str, str]) -> str:
    for token, value in subs.items():
        text = text.replace(token, value)
    return text


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    root = pathlib.Path(args[0]).resolve() if args else pathlib.Path.cwd()
    override = [a.split("=", 1)[1] for a in argv[1:] if a.startswith("--name=")]

    if not root.is_dir():
        print(f"FAIL  not a directory: {root}", file=sys.stderr)
        return 1
    if not TEMPLATE.is_dir():
        print(f"FAIL  the seed set is missing: {TEMPLATE}", file=sys.stderr)
        return 1

    short_name = override[0] if override else short_name_for(root)
    subs = substitutions(short_name)

    print(f"rite — seeding {root.name} at stage idea (short name: {short_name})")
    print()

    wrote, skipped = [], []
    for src_name, dest_name in SEEDS.items():
        src, dest = TEMPLATE / src_name, root / dest_name
        # exists_exactly, not Path.exists(): macOS and Windows are case-insensitive, so a
        # project carrying `log.md` must not be told it has no LOG.md and then given one.
        if ritefs.exists_exactly(dest):
            skipped.append(dest_name)
            continue
        dest.write_text(render(src.read_text(encoding="utf-8"), subs),
                        encoding="utf-8", newline="\n")
        wrote.append(dest_name)

    for name in wrote:
        print(f"  wrote    {name}")
    for name in skipped:
        print(f"  skipped  {name} — already present, left untouched")
    print()

    if not wrote:
        print("  Nothing to do: this project already carries the stage `idea` set.")
    else:
        print("  Read both files — the seeded LOG entry and handoff are real statements, not")
        print("  placeholders, and you should agree with what they say.")
    print()
    print("  Next: run /rite:preflight to see where the project stands. To be asked for more,")
    print("  raise `stage` in .rite.yaml — the checker will name exactly which files it wants.")
    print("  Nothing beyond stage `idea` is scaffolded: a document nobody has written cannot be")
    print("  seeded honestly.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
