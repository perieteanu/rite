import pathlib, sys
p = pathlib.Path("scripts/rite-check.py")
t = p.read_text(encoding="utf-8")
anchor = '@rule("milestones_append_only")'
rule = '''@rule("deleted_ids_appear_in_milestones")
def _deleted_ids_appear(ctx, art, test):
    """An id that left near_term must have become a milestone — or moved, not vanished.

    THE LAST DECLARED RULE TO BE IMPLEMENTED. Deleting a closed item is the convention rather
    than marking it done in place, and that is only safe if the item is PROMOTED rather than
    erased. Without this check the convention was a rule with no completion test, which is the
    one thing this project exists to abolish.

    A DELETION IS NOT ALWAYS A CLOSURE, and the check would be wrong without that. Items
    legitimately MOVE between lists: ci-portability-matrix, setup-hook-scaffolding and
    publish-github all went mid_term -> near_term on 2026-09-10, which looks identical to a
    deletion if only one list is read. So an id that left near_term is satisfied by appearing
    in milestones OR in any other roadmap list.
    """
    if not ctx.is_git:
        return NA, "requires revision history — no git repository"
    z = zone_of(ctx.root, art["path"], "near_term")
    if z is None:
        return NA, "requires revision history — file not tracked or unparseable"
    old_nt, new_nt = z

    def ids(block):
        if not isinstance(block, dict):
            return set()
        return {c.get("id") for c in (block.get("candidates") or [])
                if isinstance(c, dict) and c.get("id")}

    gone = ids(old_nt) - ids(new_nt)
    if not gone:
        return GREEN, "no near_term id was removed"

    try:
        doc = riteyaml.load((ctx.root / art["path"]).read_text(encoding="utf-8"), art["path"])
    except (riteyaml.RiteYamlError, OSError):
        return NA, "the current file could not be parsed"

    landed = {m.get("id") for m in (doc.get("milestones") or [])
              if isinstance(m, dict) and m.get("id")}
    elsewhere = set()
    for key in ("mid_term", "long_term"):
        for item in doc.get(key) or []:
            if isinstance(item, dict) and item.get("id"):
                elsewhere.add(item["id"])

    lost = sorted(i for i in gone if i not in landed and i not in elsewhere)
    if lost:
        return RED, (f"{len(lost)} near_term id(s) removed without a milestone and not moved "
                     f"to another list: {', '.join(lost)}. Deleting is how an item closes — but "
                     f"only if it is promoted, never erased.")
    moved = sorted(i for i in gone if i not in landed)
    note = f" ({len(moved)} moved, not closed)" if moved else ""
    return GREEN, f"{len(gone)} removed id(s) accounted for{note}"


@rule("milestones_append_only")'''
if t.count(anchor) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(anchor, rule, 1), encoding="utf-8", newline="\n")
print("implemented")
