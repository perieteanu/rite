import pathlib, sys
p = pathlib.Path("docs/CONCERNS.yaml")
t = p.read_text(encoding="utf-8")
before = len(t.encode("utf-8"))

for cid, nxt in (("c-pattern-paths-are-matched-literally", "  - id: c-rite-ps1-unreachable-in-production"),
                 ("c-plan-attribution", "  - id: c-freshness-thresholds-are-guesses")):
    start = t.index(f"  - id: {cid}")
    end = t.index(nxt)
    t = t[:start] + t[end:]

retired = '''retired_ids:
  - id: c-pattern-paths-are-matched-literally
    retired: "2026-09-10"
    how: settled
    outcome: d-pattern-paths-and-declared-name-shapes
    why: >
      Opened and settled the same day, and it was a PREREQUISITE rather than a neighbour: until
      an artifact could declare a glob, both of plan_copy's tests reported "not present" with
      two real plan copies on disk, so the port that needed them could not have been verified.
      Artifacts now declare `path_pattern` for presence and `canonical_name_pattern` for shape.
      The second key came out of building the first: filename_matches_canonical initially held
      the PLAN regex inside the checker, which was a hardcoded value with no human-visible home
      AND was silently wrong for the next artifact to declare the rule.

  - id: c-plan-attribution
    retired: "2026-09-10"
    how: settled
    outcome: d-attribution-is-authorship-not-mention
    why: >
      Open since 2026-09-07 as the blocker on port-mirror-memory, described as "the only
      genuinely hard part" and proposing mtime/session correlation or content inspection.
      NEITHER WAS NEEDED. Session transcripts are filed under the project slug and record the
      plan as a TOOL INPUT — a Write naming it as file_path, or an ExitPlanMode naming it as
      planFilePath. That is authorship, and it is exact.
      THE FIRST IMPLEMENTATION WAS STILL WRONG, which is the part worth keeping. Searching for
      the plan's path as a string mis-attributed five of thirteen plans, because the session
      BUILDING the attributor had run `ls ~/.claude/plans/` and its own transcript therefore
      mentioned every plan on the machine. The act of measuring changed what was measured, and
      the only reason it was caught is that the numbers disagreed with a measurement taken
      twenty minutes earlier. Nothing about the wrong answer looked wrong.
      Its narrowness is now written down rather than assumed: attribution names the project
      whose SESSION wrote the file, not the project the file is ABOUT. This repo already
      contains the counterexample — PLAN-2026-09-07-project-standard.md is rite's founding plan,
      written from a claude-persistent session because rite did not exist yet. So an existing
      copy always wins over a fresh attribution.
'''
t = t.replace("retired_ids:\n", retired, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print(f"CONCERNS.yaml: {before} -> {len(p.read_bytes())}")
