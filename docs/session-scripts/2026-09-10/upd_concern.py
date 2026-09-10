import pathlib, sys
p = pathlib.Path("docs/CONCERNS.yaml")
t = p.read_text(encoding="utf-8")
anchor = "  - id: c-readme-sample-output-is-a-copy"
new = '''  - id: c-coverage-counts-optional-as-unimplemented
    title: "The checker's coverage denominator counts `optional` markers as missing implementations"
    status: open
    severity: low
    opened: "2026-09-10"
    what: >
      rite-check.py reports "61 of 66 declared tests implemented". The gap is five INSTANCES,
      but four of them are `rule: optional` on plan_copy, script_copy, concerns and
      memory_mirror. `optional` is a marker meaning the artifact is not required; it is handled
      by an explicit branch and is deliberately absent from RULES, so the counter treats it as
      an unimplemented rule. Exactly ONE rule is genuinely unimplemented:
      deleted_ids_appear_in_milestones.
    why_it_matters: >
      It understates the checker against itself, which is the safe direction and therefore the
      easy one to leave. But four documents repeated "seven declared tests unimplemented" for
      days on the strength of this line — the number was read as a to-do list and it is not one.
      A metric that is wrong in the flattering direction gets fixed; one wrong in the modest
      direction just quietly misinforms.
    proposal:
      - "Exclude `optional` from the denominator, the way the branch already excludes it from execution."
      - "Or report both units: rules implemented, and instances run. The second is what a reader wants when deciding whether to trust a verdict."
    do_not: "Add `optional` to RULES as a no-op just to move the number. That would make the counter honest by making the code lie."

'''
if t.count(anchor) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(anchor, new + anchor, 1), encoding="utf-8", newline="\n")
print("concern opened")
