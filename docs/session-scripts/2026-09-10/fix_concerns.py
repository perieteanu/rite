import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/docs/CONCERNS.yaml")
text = p.read_text(encoding="utf-8")
before = len(text.encode("utf-8"))

# 1 — remove the open concern (it leaves via retired_ids, never silently)
start = text.index("  - id: c-stage-table-duplicated-in-three-places")
end = text.index("  - id: c-plan-attribution")
removed = text[start:end]
if "spec/project-standard.yaml is the authority" not in removed:
    sys.exit("ABORT: cut the wrong region")

new_concerns = """  - id: c-rite-ps1-unreachable-in-production
    title: "hooks/rite.ps1 is exercised by CI and by nothing in production"
    status: open
    severity: high
    opened: "2026-09-10"
    what: >
      hooks/hooks.json names `bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh"` for all three events
      and never references rite.ps1. The .ps1 exists, is a faithful translation, and passed on
      windows-latest — because CI invokes it DIRECTLY. Nothing else ever does.
    why_it_matters: >
      The spec's `coverage` list claims four rows, and the fourth — "Windows without Git for
      Windows -> PowerShell -> the .ps1 shim" — has no mechanism behind it. Such a user installs
      Rite and gets no SessionStart verdict at all. Worse than the gap is what the gate did to
      it: rite.ps1 passing on 2026-09-10 was read as evidence the path works, and a green test
      over an unreachable code path is the most expensive kind of false assurance. This project
      already has a name for it — a check that vanished and a check that passed must not look
      alike — and this is the same error one level up.
    proposal:
      - "Find out whether hooks.json can express a per-platform command, or whether Claude Code always runs hook commands through a shell it chooses."
      - "If it cannot: say so in the spec's coverage list rather than claiming the row, and make CI's invocation of rite.ps1 declare that it tests the shim and not the wiring."
    do_not: "Leave the coverage list asserting a path no user can reach. Found while correcting the neighbouring `still_unverified` claim, which had gone false for the opposite reason."

  - id: c-readme-sample-output-is-a-copy
    title: "The README's sample checker run restates the stage mapping, and nothing regenerates it"
    status: open
    severity: low
    opened: "2026-09-10"
    what: >
      README.md quotes a real run of the checker whose tail reads "46 checks not required at
      stage 'idea', waiting on: spec README.md, CLAUDE.md ... build ... shipped LICENSE". That
      is the stage mapping again, in the first document a stranger reads.
    why_it_matters: >
      It is the fifth copy, and it survived the fix that removed the other three. The
      stage-table guard deliberately exempts fenced blocks, because a guard that fires on quoted
      output would be switched off before it was fixed — so this copy is exempt by design, not
      by oversight, and it will go stale the day an artifact changes stage.
    proposal:
      - "Generate the sample by running the checker against a scratch project at render time, the way the table is generated from the spec."
      - "Or accept it and add a line to the README saying the sample is illustrative, which is cheap and honest but is a rule with no completion test."
    note: "Opened 2026-09-10 by the guard that found it. Low because the sample being slightly stale misleads nobody about what Rite does — unlike a wrong table, which someone would act on."

"""

retired = """retired_ids:
  - id: c-stage-table-duplicated-in-three-places
    retired: "2026-09-10"
    how: settled
    outcome: d-one-home-for-the-stage-mapping
    why: >
      Opened and settled the same day it was opened. Its own `do_not` named the outcome to
      avoid — "leave all three hand-maintained and rely on remembering, the rule with no
      completion test, in the repository whose thesis is that such rules fail" — and both
      halves of the proposal were taken rather than one.
      GENERATION removed the drift: README.md and template/.rite.yaml now carry a
      rite:generated block filled from artifacts[].required_from_stage, and
      `render-standard.py --blocks --check` is the gate. CLAUDE.md's copy was DELETED rather
      than generated, because it was a prose sentence mid-bullet and removing a copy beats
      mechanising it.
      A GUARD stops the next one, which generation could never do: a fresh enumeration in some
      other document is not drift from anything, so --blocks --check would never look at it.
      scripts/test-stage-table-guard.py fails when three stage names appear near three artifact
      names outside a generated block.
      TWO THINGS WERE FOUND BY BUILDING IT, both of which argue the concern understated itself.
      The count was wrong: it said three places and there were FOUR — ROADMAP.current_state
      carried the mapping too, and no one had noticed. And the README table generated
      BYTE-IDENTICAL on the first run while template/.rite.yaml did not, because the template's
      hand-written copy abbreviated `docs/MISSION.md` to `MISSION`. The copies had already
      begun to diverge.
"""

text = text[:start] + new_concerns + text[end:]
text = text.replace("retired_ids:\n", retired, 1)
p.write_text(text, encoding="utf-8", newline="\n")
print(f"CONCERNS.yaml: {before} -> {len(p.read_bytes())} bytes")
