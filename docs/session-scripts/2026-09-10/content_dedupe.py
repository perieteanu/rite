import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/scripts/rite_copy.py")
text = p.read_text(encoding="utf-8")

old = '''def _existing_plan_sources(docs: Path) -> dict[str, str]:
    """{source plan filename: copy filename} for copies that declare their provenance."""
    out: dict[str, str] = {}
    if not docs.is_dir():
        return out
    for copy in sorted(docs.glob("PLAN-*.md")):
        try:
            head = copy.read_text(encoding="utf-8", errors="replace")[:2000]
        except OSError:
            continue
        m = PLAN_PROVENANCE.search(head)
        if m:
            out[m.group("name")] = copy.name
    return out
'''
new = '''def _strip_provenance(text: str) -> str:
    """Drop a leading <!-- ... --> provenance header so a copy compares equal to its source."""
    stripped = text.lstrip()
    if stripped.startswith("<!--"):
        end = stripped.find("-->")
        if end != -1:
            return stripped[end + 3:].lstrip("\\n")
    return text


def _existing_plan_bodies(docs: Path) -> dict[str, str]:
    """{sha256 of the copied body: copy filename}.

    KEYED ON CONTENT, NOT ON SOURCE NAME, and the reason is a property of the harness rather
    than a preference: ~/.claude/plans/<name>.md is REUSED. calm-tinkering-kahan.md held this
    repo's publishing plan in the morning and its copier plan in the afternoon. Keyed on the
    source filename, the second plan would have been skipped as "already copied" and lost — the
    quiet kind of data loss, where the tool reports success.

    Content also makes the check idempotent for copies that predate any provenance header, of
    which this repo has one.
    """
    out: dict[str, str] = {}
    if not docs.is_dir():
        return out
    for copy in sorted(docs.glob("PLAN-*.md")):
        try:
            body = _strip_provenance(copy.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        out[hashlib.sha256(body.encode("utf-8")).hexdigest()] = copy.name
    return out
'''
if text.count(old) != 1:
    sys.exit("ABORT: _existing_plan_sources not found")
text = text.replace(old, new, 1)

old_use = '''    already = _existing_plan_sources(docs)'''
new_use = '''    already = _existing_plan_bodies(docs)'''
text = text.replace(old_use, new_use, 1)

old_skip = '''        if plan.name in already:
            report.add("have", plan.name, f"already copied as {already[plan.name]}")
            continue

        body = plan.read_text(encoding="utf-8")
'''
new_skip = '''        body = plan.read_text(encoding="utf-8")
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if digest in already:
            report.add("have", plan.name, f"content already copied as {already[digest]}")
            continue

'''
if text.count(old_skip) != 1:
    sys.exit("ABORT: skip block not found")
text = text.replace(old_skip, new_skip, 1)
text = text.replace("import datetime as dt\nimport json", "import datetime as dt\nimport hashlib\nimport json", 1)

p.write_text(text, encoding="utf-8", newline="\n")
print("patched")
