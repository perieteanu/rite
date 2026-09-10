import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/docs/CONCERNS.yaml")
text = p.read_text(encoding="utf-8")
anchor = "  - id: c-rite-ps1-unreachable-in-production"
if text.count(anchor) != 1:
    sys.exit("ABORT: anchor not found")
new = '''  - id: c-pattern-paths-are-matched-literally
    title: "plan_copy declares a PATTERN as its path, and the checker compares it as a literal"
    status: open
    severity: high
    opened: "2026-09-10"
    what: >
      The plan_copy artifact declares path "docs/PLAN-YYYY-MM-DD-<slug>.md". rite-check.py
      computes presence as `ctx.exists_exactly(art["path"])` — a case-sensitive literal
      comparison — so it looks for a file whose name contains the characters YYYY-MM-DD and
      <slug>. No such file can exist, so plan_copy is reported "tier 2, not present — optional"
      forever, on every project, whatever it actually contains.
    evidence: >
      Found 2026-09-10 by copying this session's plan to docs/PLAN-2026-09-10-publish-github.md
      beside the existing docs/PLAN-2026-09-07-project-standard.md. TWO plan files present; the
      checker still printed "not present" for both of its tests.
    why_it_matters: >
      filename_matches_canonical exists to check that a plan copy is NAMED correctly, and it has
      never once run against a plan file — it cannot. source_plans_all_copied is listed among the
      seven unimplemented tests, which is generous: it is not merely unimplemented, its artifact
      is unreachable. This is the third member of a family found in one day, after
      python_invocation_differs (declared, enforced by nothing) and rite.ps1 (tested, unreachable
      in production). All three read as covered and are not, which is worse than a visible gap.
    proposal:
      - "Give an artifact an optional `path_pattern` (glob) distinct from `path`, and let presence be a glob match when it is set. `path` stays the canonical display name."
      - "Then filename_matches_canonical has something to check: every file matching the glob must also match the canonical shape, which is the test as originally intended."
    do_not: "Rename the artifact to a literal path. There are legitimately many plan copies per project — that is stated in CLAUDE.md — and one canonical filename would be a worse lie than the current silence."

'''
p.write_text(text.replace(anchor, new + anchor, 1), encoding="utf-8", newline="\n")
print("CONCERNS.yaml updated")
