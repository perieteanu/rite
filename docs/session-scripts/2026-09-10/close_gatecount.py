import pathlib, sys
# retire the concern
p = pathlib.Path("docs/CONCERNS.yaml")
t = p.read_text(encoding="utf-8")
start = t.index("  - id: c-gate-count-restated-in-prose")
end = t.index("  - id: c-readme-sample-output-is-a-copy")
t = t[:start] + t[end:]
retired = '''retired_ids:
  - id: c-gate-count-restated-in-prose
    retired: "2026-09-10"
    how: settled
    outcome: d-one-home-for-the-gate-count
    why: >
      Opened and settled the same day, hours apart, on the evidence of its own failure: the
      count went 9 -> 11 -> 12 -> 13 within one day and each move falsified four or five
      sentences. Settled the same way as c-stage-table-duplicated-in-three-places — generate
      where the number earns its place, DELETE where it does not.
      README and ARCHITECTURE now carry rite:generated blocks fed from .github/gates.yaml.
      CLAUDE.md's and ROADMAP.current_state's copies were deleted and point at the file instead,
      because neither reader needs a count — they need to know where the gates are declared,
      which is the more durable fact.
      The block mechanism gained `source_file` to make this possible; until today every block
      generated from the standard alone. A generator reaching into the spec for the gate list
      would have recreated the copy it exists to remove.
      Proved by adding a fictional 14th gate to the authority: both documents were flagged
      stale, the count moved 13 -> 14 and 3 -> 4 and "10 of 14" adjusted itself, with no
      document edited by hand.

'''
t = t.replace("retired_ids:\n", retired, 1)
p.write_text(t, encoding="utf-8", newline="\n")

# decision
d = pathlib.Path("docs/DECISIONS.yaml")
entry = '''
  - id: d-one-home-for-the-gate-count
    date: "2026-09-10"
    title: "The gate count is generated where it earns its place and deleted where it does not"
    context: >
      .github/gates.yaml is the authority for the gate list, and the COUNT was hand-copied into
      README, CLAUDE.md, docs/ARCHITECTURE.md and ROADMAP.current_state. It went 9 -> 11 -> 12
      -> 13 in a single day; each move falsified four or five sentences, and the last also moved
      a second derived number, the skip count. On the final pass README still opened "Nine gates
      run on every push" above a corrected total.
    decision: >
      Two rite:generated blocks fed from .github/gates.yaml — `gate-counts` into README and
      `gate-list` into ARCHITECTURE. CLAUDE.md's and ROADMAP.current_state's copies are DELETED
      and point at the file. `generated_blocks` gains `source_file`, so a block may generate
      from something other than the standard.
    rationale:
      - >
        GENERATE WHERE THE NUMBER EARNS ITS PLACE, DELETE WHERE IT DOES NOT. A stranger reading
        the README is deciding whether to care and a count helps. An agent reading CLAUDE.md and
        a session reading current_state need to know WHERE the gates are declared, which is more
        durable than how many there are. Fewest copies wins, exactly as with the stage table.
      - >
        THE SKIPPED COUNT NEEDS NO SECOND SOURCE. A gate declaring `skip_short` is a gate that
        can skip, so both numbers and every reason come from one file. `skip_short` was added
        beside the existing `skip_means` — the same fact in one clause, for prose.
      - >
        `source_file` IS THE GENERAL FIX. Every block until today generated from the standard,
        which would have forced the gate list into spec/project-standard.yaml to be readable —
        recreating the copy the block exists to remove. Blocks are now source-agnostic.
    evidence: >
      Proved by adding a fictional 14th gate to .github/gates.yaml. Both documents were flagged
      stale, the count moved 13 -> 14 and 3 -> 4, and "10 of 13" became "10 of 14" — with no
      document edited by hand. Restored byte-identical afterwards.
    chosen_by_user: true
    proposed_by: claude
'''
d.write_text(d.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry, encoding="utf-8", newline="\n")
print("concern retired, decision appended")
