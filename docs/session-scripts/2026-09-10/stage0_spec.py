import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/spec/project-standard.yaml")
text = p.read_text(encoding="utf-8")
before = len(text.encode("utf-8"))

# 1 — document path_pattern where artifacts are introduced
old_head = "# ── artifacts ────────────────────────────────────────────────────────────────\nartifacts:\n"
new_head = '''# ── artifacts ────────────────────────────────────────────────────────────────
# `path` is the canonical name and what a finding displays. Where an artifact legitimately has
# MANY instances under generated names, it also declares `path_pattern`, a glob, and presence is
# a glob match instead of a literal one.
#
# WHY THIS FIELD EXISTS, since a second path key looks like duplication: plan_copy declared
# path "docs/PLAN-YYYY-MM-DD-<slug>.md" and the checker compared it with exists_exactly — a
# literal, case-sensitive test. No file can be named YYYY-MM-DD, so plan_copy reported
# "not present" on every project forever, and filename_matches_canonical — the test whose whole
# job is to check that a plan copy is NAMED correctly — had never once run against a plan file
# and could not. Found 2026-09-10 with two real plan copies sitting on disk beside the verdict
# that said there were none. c-pattern-paths-are-matched-literally.
#
# Renaming the artifact to a literal path was the WRONG fix and was rejected: there are
# legitimately many plan copies per project, and one canonical filename would be a worse lie
# than the silence it replaced.
artifacts:
'''
if text.count(old_head) != 1:
    sys.exit("ABORT: artifacts header not found")
text = text.replace(old_head, new_head, 1)

# 2 — plan_copy declares the pattern
old_pc = '''  - id: plan_copy
    path: "docs/PLAN-YYYY-MM-DD-<slug>.md"
    write_discipline: write_once
'''
new_pc = '''  - id: plan_copy
    path: "docs/PLAN-YYYY-MM-DD-<slug>.md"
    path_pattern: "docs/PLAN-*.md"
    write_discipline: write_once
'''
if text.count(old_pc) != 1:
    sys.exit("ABORT: plan_copy not found")
text = text.replace(old_pc, new_pc, 1)

p.write_text(text, encoding="utf-8", newline="\n")
print(f"project-standard.yaml: {before} -> {len(p.read_bytes())} bytes")
