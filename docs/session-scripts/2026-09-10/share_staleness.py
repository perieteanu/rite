import pathlib, sys
p = pathlib.Path("scripts/rite_copy.py")
t = p.read_text(encoding="utf-8")

anchor = "def mirror_memory(root: Path, dry_run: bool) -> Report:"
helper = '''MIRROR_STAMP = re.compile(r"^> Last sync: (\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2})$", re.MULTILINE)

# The stamp has minute resolution, so a memory written in the same minute as the sync is not
# evidence of staleness. Only a file newer than the END of that minute counts.
STAMP_RESOLUTION = dt.timedelta(minutes=1)


def mirror_stamp(text: str) -> dt.datetime | None:
    m = MIRROR_STAMP.search(text)
    if not m:
        return None
    try:
        return dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def mirror_is_stale(root: Path, text: str, files: list[Path]) -> bool | None:
    """Is this mirror older than the memories it claims to mirror? None = cannot tell.

    SHARED WITH THE CHECKER on purpose, and the reason is a bug this had on its first run. The
    copier skipped rewriting whenever the CONTENT matched, ignoring the stamp; the checker
    judged staleness from the STAMP alone. So a mirror with a stale stamp and correct content
    was YELLOW forever, and the checker's own advice — "run rite_copy.py --memory" — did
    nothing. Two implementations of one predicate is the drift this project exists to attack,
    and it took under an hour to prove it on itself.
    """
    stamp = mirror_stamp(text)
    if stamp is None or not files:
        return None
    newest = max(f.stat().st_mtime for f in files)
    return newest > (stamp + STAMP_RESOLUTION).timestamp()


def mirror_memory(root: Path, dry_run: bool) -> Report:'''
if t.count(anchor) != 1:
    sys.exit("ABORT: mirror_memory anchor")
t = t.replace(anchor, helper, 1)

old = '''        strip = lambda s: re.sub(r"^> Last sync: .*$", "", s, flags=re.MULTILINE)  # noqa: E731
        if strip(current) == strip(text):
            report.add("current", target.name, f"{len(files)} memories, unchanged")
            return report
'''
new = '''        strip = lambda s: MIRROR_STAMP.sub("", s)  # noqa: E731
        stale = mirror_is_stale(root, current, files)
        if strip(current) == strip(text) and stale is False:
            report.add("current", target.name, f"{len(files)} memories, unchanged")
            return report
        if strip(current) == strip(text):
            # Content matches but the stamp does not vouch for it. Rewriting refreshes the
            # stamp, which is the only thing mirror_not_stale can read.
            report.add("restamped", target.name, f"{len(files)} memories, sync stamp refreshed")
            if not dry_run:
                target.write_text(text, encoding="utf-8", newline="\\n")
            return report
'''
if t.count(old) != 1:
    sys.exit("ABORT: comparison block")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("rite_copy patched")
