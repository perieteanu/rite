import pathlib, sys
p = pathlib.Path("docs/ROADMAP.yaml")
t = p.read_text(encoding="utf-8")
before = len(t.encode("utf-8"))

# 1 — DELETE the item from mid_term
old_item = '''  - id: port-mirror-memory
    what: "Port claude-mirror-memory.py; extend the same tool to plan copying"
    why: "Plans are the identical problem with a different source dir. One tool, not two."
'''
if t.count(old_item) != 1:
    sys.exit("ABORT: port-mirror-memory item not found")
t = t.replace(old_item, "", 1)

# 2 — the watcher's premise has changed; say so where it is declared
old_w = '''    why: >
      CLOSES c-plan-attribution. That problem is only hard retroactively — a plan copied at
      creation belongs to the project the session is in. Attribution by timing, not by content
      inspection.
    unverified: "that FileChanged watches paths outside the project root"'''
new_w = '''    why: >
      Originally justified as the thing that CLOSES c-plan-attribution, on the premise that the
      problem "is only hard retroactively". THAT PREMISE IS GONE as of 2026-09-10:
      d-attribution-is-authorship-not-mention attributes a plan exactly, after the fact, from
      the transcript that wrote it. This item is now an OPTIMISATION — it buys latency, so a
      plan is copied even if the session never reaches /rite:end — and nothing depends on it.
    unverified: "that FileChanged watches paths outside the project root"'''
if t.count(old_w) != 1:
    sys.exit("ABORT: watcher rationale not found")
t = t.replace(old_w, new_w, 1)

# 3 — APPEND the milestone
milestone = '''  - id: port-mirror-memory
    what: "One copier for three sources — memory mirror, plan copy, session-script copy"
    closed: "2026-09-10"
    log_ref: "10-09-2026"
    note: >
      Taken from mid_term rather than near_term, which was empty by design after publishing.
      The item's own note set the shape — "Plans are the identical problem with a different
      source dir. One tool, not two." — and a third source joined them: the helper scripts a
      session writes to its scratchpad, which lives in /tmp and does not survive a reboot.
      ITS BLOCKER WAS NEVER HARD. c-plan-attribution had sat since 2026-09-07 as "the only
      genuinely hard part", proposing mtime correlation or content inspection. Session
      transcripts record a plan as a TOOL INPUT, so authorship is exact and neither was needed.
      THE FIRST ATTRIBUTOR WAS STILL WRONG, and that is the part worth remembering. Matching the
      plan's path as a string mis-attributed five of thirteen plans, because the session BUILDING
      it had run `ls ~/.claude/plans/` and its transcript therefore mentioned every plan on the
      machine. The act of measuring changed what was measured, and it was caught only because
      the numbers disagreed with a shell measurement taken twenty minutes earlier.
      THREE MORE DECLARED TESTS ARE NOW IMPLEMENTED — filename_matches_canonical,
      source_plans_all_copied and mirror_not_stale — taking coverage from 57 of 64 to 61 of 66,
      and all three were proved to FAIL before being trusted. Two of them were UNREACHABLE
      rather than merely unwritten until path_pattern existed, which is why
      c-pattern-paths-are-matched-literally had to be settled first.
      The memory port is byte-compatible with the script it replaces: regenerated output differs
      from the global hook's only in the clock. The global hook is deliberately left running
      beside it until the port is proven.

'''
anchor = "near_term:\n"
if t.count(anchor) != 1:
    sys.exit("ABORT: near_term anchor")
t = t.replace(anchor, milestone + anchor, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print(f"ROADMAP.yaml: {before} -> {len(p.read_bytes())}")
