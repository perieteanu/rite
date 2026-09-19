#!/usr/bin/env python3
"""rite_init — seed a project so it opens on GREEN at stage `idea`.

WHAT IT WRITES, AND WHY IT REFUSES TO WRITE MORE. Four files: .rite.yaml, LOG.md, HANDOFF.md and
a .gitignore. The first three are exactly what stage `idea` requires, and `idea` is the only stage
whose requirements a machine can satisfy HONESTLY:

  - a LOG carrying one real entry IS a complete log
  - a HANDOFF with `genre: none` IS a complete handoff — the standard says so outright: a real
    answer, the assertion that none is needed, made by someone who considered the question

Nothing else qualifies. A seeded MISSION.md that nobody has written is a lie that passes
file_present, and the `populated` tests cannot tell a filled template from an unfilled one —
give it enough headings and it scores. Seeding prose would manufacture precisely the
confidently-wrong document this project exists to attack, and would do it at first contact.
So advancing past `idea` stays a human act, and the checker names exactly which files it wants.

THE .gitignore IS NOT A STAGE REQUIREMENT — it is a DEFAULT, and the one file here that protects
rather than satisfies. Three of the standard's artifacts are copies Rite makes out of ~/.claude
rather than things the user wrote, and on 2026-09-19 this project found its own mirrored memory
publishing a contributor's SSH host aliases, private-key filenames and second account to a public
repository. It was tracked deliberately, for auditability, by the person who wrote the standard.
So the rule "the user decides what to publish" was tested in the most informed hands available and
failed — auditability is served by the file EXISTING, never by it being pushed. Rite never
publishes what it copied out of the agent's private space; only what you wrote yourself. The
ignore rules are seeded, explained in the file, and reversible by deleting them. An existing
.gitignore is never edited: the paths are printed instead, for the user to paste or refuse.

NEVER OVERWRITES. An existing file is left alone and reported as skipped, so the command is safe
to re-run and re-running is the intended use. It does not touch ~/.claude, install anything, or
run git — see d-never-instruct-installation.

Run:  <python> scripts/rite_init.py [PROJECT_DIR] [--name=SHORT_NAME]
      From a skill or a user: bash hooks/rite.sh init [PROJECT_DIR] [--name=SHORT_NAME]
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
import riterules  # noqa: E402

ritefs.use_utf8_stdio()

TEMPLATE = ROOT / "template"
SPEC_PATH = ROOT / "spec" / "project-standard.yaml"

# Which template file lands where. The marker's name comes from ritefs so there is one spelling
# of it in the codebase rather than three.
SEEDS = {
    ".rite.yaml": ritefs.MARKER,
    "LOG.md": "LOG.md",
    "HANDOFF.md": "HANDOFF.md",
    # Seeded WITHOUT its dot. A file named template/.gitignore would be live git configuration
    # for the template directory itself rather than inert seed text — harmless while the paths
    # stay under docs/, a trap the day someone widens one. The destination name carries the dot.
    "gitignore": ".gitignore",
}

# The seed whose absence is a protection failure rather than a missing document, named once.
GITIGNORE_SEED = "gitignore"

# The artifacts the seeded .gitignore covers: the three Rite COPIES out of ~/.claude, as opposed
# to the ones the user writes. Ids, never paths — the paths are resolved from the standard, so a
# project declaring a legacy documentation directory is given ignore rules pointing at its own.
AGENT_COPY_ARTIFACTS = ("memory_mirror", "plan_copy", "script_copy")

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


def agent_copy_ignores(root: pathlib.Path) -> list[str]:
    """Ignore rules for the three artifacts Rite copies out of ~/.claude, resolved from the spec.

    Empty when the standard cannot be read or declares none of them. The caller must treat that
    as a reason to SKIP the file and say so: a .gitignore seeded with a header and no rules would
    read as protection while protecting nothing, and it fails in the direction that publishes.
    """
    spec = riterules.load_spec(SPEC_PATH)
    marker = riterules.read_marker(root)
    rules = []
    for artifact_id in AGENT_COPY_ARTIFACTS:
        declared = riterules.artifact_path(spec, artifact_id, marker)
        if declared:
            rules.append(riterules.ignore_pattern(declared))
    return rules


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
    ignores = agent_copy_ignores(root)
    subs["{{AGENT_COPY_IGNORES}}"] = "\n".join(ignores)

    print(f"rite — seeding {root.name} at stage idea (short name: {short_name})")
    print()

    wrote, skipped, unresolved = [], [], []
    for src_name, dest_name in SEEDS.items():
        src, dest = TEMPLATE / src_name, root / dest_name
        # exists_exactly, not Path.exists(): macOS and Windows are case-insensitive, so a
        # project carrying `log.md` must not be told it has no LOG.md and then given one.
        if ritefs.exists_exactly(dest):
            skipped.append(dest_name)
            continue
        # A .gitignore with a header and no rules would READ as protection while protecting
        # nothing. Refuse rather than seed one, and say which is the case.
        if src_name == GITIGNORE_SEED and not ignores:
            unresolved.append(dest_name)
            continue
        dest.write_text(render(src.read_text(encoding="utf-8"), subs),
                        encoding="utf-8", newline="\n")
        wrote.append(dest_name)

    for name in wrote:
        print(f"  wrote    {name}")
    for name in skipped:
        print(f"  skipped  {name} — already present, left untouched")
    for name in unresolved:
        print(f"  skipped  {name} — the standard declared no agent-copy paths to ignore")
    print()

    if not wrote:
        print("  Nothing to do: this project already carries the stage `idea` set.")
    elif {"LOG.md", "HANDOFF.md"} & set(wrote):
        print("  Read the seeded LOG entry and handoff — they are real statements, not")
        print("  placeholders, and you should agree with what they say.")
    print()

    # THE DISCLOSURE, printed whether or not the file was written. A user who learns what Rite
    # copies only by finding it in a diff has learned it too late; this project's own mirrored
    # memory reached a public repository exactly that way.
    if ignores:
        print("  Rite copies three things out of Claude's private area (~/.claude) into this")
        print("  project, so you can audit what the agent kept:")
        for rule in ignores:
            print(f"    {rule}")
        if ".gitignore" in wrote:
            print("  They are ignored by default. Publishing your own work record is a choice,")
            print("  not something adopting a standard should make for you — delete those lines")
            print("  from .gitignore if you want them in the repository.")
        else:
            print("  This project already has a .gitignore and Rite did not touch it. Add the")
            print("  lines above yourself if you would rather those copies stayed unpublished.")
        print()
    print("  Next: run /rite:preflight to see where the project stands. To be asked for more,")
    print("  raise `stage` in .rite.yaml — the checker will name exactly which files it wants.")
    print("  Nothing beyond stage `idea` is scaffolded: a document nobody has written cannot be")
    print("  seeded honestly.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
