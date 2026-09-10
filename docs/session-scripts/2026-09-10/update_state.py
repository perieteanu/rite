import pathlib, sys
p = pathlib.Path("docs/ROADMAP.yaml")
t = p.read_text(encoding="utf-8")
old = "  STILL TRUE AND WORTH SAYING PLAINLY: no one but this machine has run Rite. Publishing changed\n  who CAN, not who HAS.\n"
new = ('''  THE COPIERS ARE PORTED — one tool, three sources, scripts/rite_copy.py. The memory mirror is a
  port rather than a rewrite: its output differs from the global hook's only in the clock, and
  that hook is deliberately left running beside it until the port is proven. Plan copy and
  session-script copy join it, because the sources differ and the spine does not.
  ATTRIBUTION IS AUTHORSHIP, NOT MENTION, and the distinction cost five of thirteen plans before
  it was drawn. c-plan-attribution is settled — d-attribution-is-authorship-not-mention — after
  three days as "the only genuinely hard part". It was never hard; the FIRST ANSWER was just
  wrong in a way nothing looked wrong about.
  COVERAGE IS 61 OF 66 declared tests, up from 57 of 64. filename_matches_canonical,
  source_plans_all_copied and mirror_not_stale are implemented, and the first two were
  UNREACHABLE rather than unwritten until an artifact could declare a path_pattern.
  THE INVENTORY IS 14, not 13. script_copy was added through the process the freeze exists to
  force — a DECISIONS entry — rather than around it.
  STILL TRUE AND WORTH SAYING PLAINLY: no one but this machine has run Rite. Publishing changed
  who CAN, not who HAS.
''')
if t.count(old) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("current_state updated")
