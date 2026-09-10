import pathlib, sys
p = pathlib.Path("scripts/rite-check.py")
t = p.read_text(encoding="utf-8")
old_start = t.index('    stamp = re.search(r"^> Last sync: ')
old_end = t.index('    return GREEN, f"{len(files)} memories, synced {stamp.group(1)}"') + len('    return GREEN, f"{len(files)} memories, synced {stamp.group(1)}"\n')
new = '''    files = rite_copy.memory_files(memdir)
    if not files:
        return NA, "no memory files"
    stamp = rite_copy.mirror_stamp(text)
    if stamp is None:
        return YELLOW, "no readable `Last sync` line — cannot tell whether this mirror is current"
    # ONE PREDICATE, shared with the copier. Two implementations disagreed within the hour they
    # both existed: the copier skipped rewriting when content matched and the checker judged by
    # the stamp, so a stale stamp over correct content stayed YELLOW and the checker's own
    # advice fixed nothing.
    if rite_copy.mirror_is_stale(memdir.parent, text, files):
        when = dt.datetime.fromtimestamp(max(f.stat().st_mtime for f in files))
        return YELLOW, (f"a memory changed at {when:%Y-%m-%d %H:%M}, after the mirror synced at "
                        f"{stamp:%Y-%m-%d %H:%M} — run rite_copy.py --memory")
    return GREEN, f"{len(files)} memories, synced {stamp:%Y-%m-%d %H:%M}"
'''
p.write_text(t[:old_start] + new + t[old_end:], encoding="utf-8", newline="\n")
print("checker patched")
