import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/docs/ROADMAP.yaml")
text = p.read_text(encoding="utf-8")
before = len(text.encode("utf-8"))

# 1 — APPEND the milestone, immediately before near_term:
milestone = '''  - id: publish-github
    what: "The repository made public, main in full, stage advanced to shipped in the same commit"
    closed: "2026-09-10"
    log_ref: "10-09-2026"
    note: >
      The last of the four items of the path from private to public, and the only one that was
      a decision rather than a task. Three acts in one commit, as the checklist demanded:
      visibility flipped, stage advanced from `build` to `shipped`, and the LICENSE check
      thereby turned live.
      THE CHECKLIST'S THIRD ACT WAS BASED ON A FALSE PREMISE, found by verifying it instead of
      performing it. It said the LICENSE check "currently reports NA" and to confirm it went
      GREEN and not RED. It was already GREEN at `build`, and had been all along:
      required_from_stage gates whether an artifact is DEMANDED, not whether it is CHECKED when
      present. CLAUDE.md and d-stage-advances-when-the-repo-goes-public both asserted the NA.
      A checker run against a `stage: shipped` copy of the tree settled it in one command —
      61 checks, 0 RED, before and after.
      TWO DEFECTS WERE FOUND ON THE WAY OUT and fixed before publishing, which is the argument
      for treating a publish as a review rather than a setting. python_invocation_differs was
      declared in the spec and enforced by nothing, and two shipped SKILL.md prompts violated
      it — the rule's own worst case, since a skill prompt is a command a Windows user's agent
      runs. And the stage mapping had four hand-maintained copies, one more than the concern
      counted. Both now have gates. The repository went public at eleven gates green rather
      than nine.

'''
anchor = "near_term:\n"
if text.count(anchor) != 1:
    sys.exit(f"ABORT: near_term anchor matched {text.count(anchor)} times")
text = text.replace(anchor, milestone + anchor, 1)

# 2 — DELETE the item from near_term; the list is now empty
start = text.index("near_term:\n")
end = text.index("mid_term:\n")
near_term = text[start:end]
if "publish-github" not in near_term:
    sys.exit("ABORT: publish-github not found inside near_term")

replacement = '''near_term:
  label: "EMPTY — the path from private to public is complete"
  # Emptied 2026-09-10, and empty ON PURPOSE rather than by omission. All four items —
  # ci-portability-matrix, setup-hook-scaffolding, readme-for-a-stranger and publish-github —
  # were queued and closed the same day, each one closed by DELETING it here and APPENDING a
  # milestones entry naming its id. The next move is a decision about direction, not a queued
  # task; mid_term below is where the candidates are, and the HANDOFF says which of them the
  # session that closed this one would pick.
  candidates: []

'''
text = text[:start] + replacement + text[end:]
p.write_text(text, encoding="utf-8", newline="\n")
print(f"ROADMAP.yaml: {before} -> {len(p.read_bytes())} bytes")
