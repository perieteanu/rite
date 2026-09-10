import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/scripts/rite_copy.py")
text = p.read_text(encoding="utf-8")
old = """    for plan in plans:
        slug = index.get(plan.name)
        if slug is None:
            report.add("UNATTRIBUTED", plan.name, "no transcript names it — skipped, never guessed")
            continue
        if slug not in mine:
            report.add("elsewhere", plan.name, f"belongs to {slug} — not written")
            continue
"""
new = """    for plan in plans:
        owners = index.get(plan.name) or set()
        if not owners:
            report.add("UNATTRIBUTED", plan.name,
                       "no session is recorded writing it — skipped, never guessed")
            continue
        if len(owners) > 1 and not (owners & mine):
            report.add("AMBIGUOUS", plan.name,
                       "authored in " + ", ".join(sorted(owners)) + " — not written")
            continue
        if not (owners & mine):
            report.add("elsewhere", plan.name,
                       f"belongs to {sorted(owners)[0]} — not written")
            continue
"""
if text.count(old) != 1:
    sys.exit(f"ABORT: matched {text.count(old)}")
text = text.replace(old, new, 1).replace("import argparse\nimport datetime as dt",
                                          "import argparse\nimport datetime as dt\nimport json", 1)
p.write_text(text, encoding="utf-8", newline="\n")
print("patched")
