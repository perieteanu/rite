import pathlib, sys
p = pathlib.Path("docs/CONCERNS.yaml")
t = p.read_text(encoding="utf-8")
anchor = "  - id: c-rite-ps1-unreachable-in-production"
new = '''  - id: c-gate-count-restated-in-prose
    title: "The gate count has one true home and is hand-copied into four documents"
    status: open
    severity: high
    opened: "2026-09-10"
    what: >
      .github/gates.yaml is the authority — the runner reads it, and it says so in its own
      preamble. The COUNT of gates, and the count that can skip on a runner, are then written
      out as prose in README.md, CLAUDE.md, docs/ARCHITECTURE.md and ROADMAP.current_state.
    evidence: >
      It went 9 -> 11 -> 12 -> 13 in a single day, and every change falsified four or five
      sentences at once. The last round also moved the SKIP count 2 -> 3, which is a second
      derived number in the same sentences. On the final pass README.md still opened "Nine
      gates run on every push" directly above a corrected total, three edits after the number
      first moved.
    why_it_matters: >
      THIS IS NOW THE MOST-REPEATED FAILURE IN THIS REPOSITORY'S HISTORY, and it is the same
      shape as c-stage-table-duplicated-in-three-places, which was settled today: a value with
      one true home, hand-copied into prose that nobody re-checks. The claim surface cannot
      catch it — claims_match_filesystem checks PATHS, not values, and said so while every
      number around it was wrong. The stage-table guard cannot either; it guards one specific
      mapping.
    proposal:
      - "Generate the counts into a rite:generated block fed from .github/gates.yaml, the way the stage table is fed from the spec. The mechanism already exists and this is what it is for."
      - "The skip count comes free from the same source: a gate declaring skip_means is a gate that can skip."
      - "Or widen the claim surface from paths to VALUES, which is the more general fix and a much larger one."
    do_not: >
      Rely on remembering to grep for the number. That was the practice all day and it failed
      three times out of three, in the repository whose thesis is that such practices fail.

'''
if t.count(anchor) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(anchor, new + anchor, 1), encoding="utf-8", newline="\n")
print("concern opened")
