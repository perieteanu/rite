import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/scripts/rite-check.py")
text = p.read_text(encoding="utf-8")
before = len(text.encode("utf-8"))

anchor = '@rule("claims_declared")'
block = '''CANONICAL_PLAN_NAME = re.compile(r"^PLAN-\\d{4}-\\d{2}-\\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\\.md$")


@rule("filename_matches_canonical")
def _filename_matches_canonical(ctx, art, test):
    """Every instance of a many-instance artifact is named the canonical way.

    Reachable only since path_pattern existed. Before that the artifact was matched literally
    against "docs/PLAN-YYYY-MM-DD-<slug>.md", so this rule had never once run against a real
    plan copy — c-pattern-paths-are-matched-literally.
    """
    pattern = art.get("path_pattern")
    if not pattern:
        return NA, "artifact declares no path_pattern"
    found = ctx.glob_matches(pattern)
    if not found:
        return NA, "no instances present"
    bad = [f for f in found if not CANONICAL_PLAN_NAME.match(f.rsplit("/", 1)[-1])]
    if bad:
        shape = art.get("structure", {}).get("canonical_name", "the canonical shape")
        return YELLOW, f"{len(bad)} of {len(found)} not named {shape}: " + ", ".join(bad)
    return GREEN, f"{len(found)} instance(s) canonically named"


@rule("source_plans_all_copied")
def _source_plans_all_copied(ctx, art, test):
    """A plan this project's own session WROTE, with no copy here, fails.

    Attribution is authorship, never mention: a transcript that merely lists the plans
    directory does not own its contents. See rite_copy._authored_in, which learned that the
    hard way.
    """
    try:
        import rite_copy
    except ImportError as exc:
        return NA, f"cannot load the copier — {exc}"
    if not rite_copy.PLANS_DIR.is_dir():
        return NA, "no plans directory on this machine"
    missing = rite_copy.uncopied_plans(ctx.root)
    if missing is None:
        return NA, "no session transcripts to attribute against"
    if missing:
        return YELLOW, (f"{len(missing)} plan(s) written by this project are not copied here: "
                        + ", ".join(missing) + " — run rite_copy.py --plans")
    return GREEN, "every plan this project wrote has a copy here"


@rule("mirror_not_stale")
def _mirror_not_stale(ctx, art, test):
    """A memory newer than the mirror's last sync means the mirror is lying by omission."""
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    try:
        import rite_copy
    except ImportError as exc:
        return NA, f"cannot load the copier — {exc}"
    memdir = rite_copy.memory_dir_for(ctx.root)
    if memdir is None:
        return NA, "no memory folder for this project"
    stamp = re.search(r"^> Last sync: (\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2})$", text, re.MULTILINE)
    if not stamp:
        return YELLOW, "no `Last sync` line — cannot tell whether this mirror is current"
    try:
        synced = datetime.datetime.strptime(stamp.group(1), "%Y-%m-%d %H:%M")
    except ValueError:
        return YELLOW, f"unreadable sync stamp {stamp.group(1)!r}"
    files = rite_copy.memory_files(memdir)
    if not files:
        return NA, "no memory files"
    # The stamp has minute resolution, so a memory written in the same minute as the sync is
    # not evidence of staleness. Only a file newer than the END of that minute counts.
    newest = max(f.stat().st_mtime for f in files)
    if newest > (synced + datetime.timedelta(minutes=1)).timestamp():
        when = datetime.datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M")
        return YELLOW, (f"a memory changed at {when}, after the mirror synced at "
                        f"{stamp.group(1)} — run rite_copy.py --memory")
    return GREEN, f"{len(files)} memories, synced {stamp.group(1)}"


@rule("claims_declared")'''

if text.count(anchor) != 1:
    sys.exit("ABORT: anchor not unique")
text = text.replace(anchor, block, 1)
p.write_text(text, encoding="utf-8", newline="\n")
print(f"rite-check.py: {before} -> {len(p.read_bytes())} bytes")
