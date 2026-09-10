import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/scripts/rite_copy.py")
text = p.read_text(encoding="utf-8")
anchor = "def copy_plans(root: Path, dry_run: bool) -> Report:"
helper = '''def uncopied_plans(root: Path) -> list[str] | None:
    """Plans this project's session AUTHORED that have no copy in docs/.

    The read-only half of copy_plans, shared so the checker and the copier can never disagree
    about what "copied" means — two implementations of one predicate is the drift this project
    exists to attack. Returns None when there are no transcripts to attribute against, which is
    NA rather than a pass: nothing was checked.
    """
    if not _transcripts():
        return None
    docs = root / DOCS
    plans = sorted(PLANS_DIR.glob("*.md")) if PLANS_DIR.is_dir() else []
    index = build_attribution_index({q.name for q in plans})
    mine = set(slug_candidates(root))
    already = _existing_plan_bodies(docs)
    missing: list[str] = []
    for plan in plans:
        if not (index.get(plan.name) or set()) & mine:
            continue
        try:
            body = plan.read_text(encoding="utf-8")
        except OSError:
            continue
        if hashlib.sha256(body.encode("utf-8")).hexdigest() not in already:
            missing.append(plan.name)
    return missing


def copy_plans(root: Path, dry_run: bool) -> Report:'''
if text.count(anchor) != 1:
    sys.exit("ABORT")
p.write_text(text.replace(anchor, helper, 1), encoding="utf-8", newline="\n")
print("added uncopied_plans")
