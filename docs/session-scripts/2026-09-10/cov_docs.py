import pathlib, sys
edits = [
("README.md",
 "- **One of the standard's declared rules is unimplemented** — `deleted_ids_appear_in_milestones`\n"
 "  — and the report says so on every run instead of quietly scoring what it can. The coverage\n"
 "  line reads `61 of 66` because its denominator counts test INSTANCES and includes four\n"
 "  `optional` markers, which are not rules awaiting implementation\n"
 "  (`c-coverage-counts-optional-as-unimplemented`).\n",
 "- **One of the standard's declared rules is unimplemented** — `deleted_ids_appear_in_milestones`\n"
 "  — and the report says so on every run instead of quietly scoring what it can.\n"),
("docs/ARCHITECTURE.md",
 "                     tests. 62 checks on this project; 61 of 66 declared tests implemented.",
 "                     tests. 62 checks on this project; 61 of 62 declared tests implemented."),
("docs/ROADMAP.yaml",
 "  checker's coverage line reads 61 of 66 because its denominator counts test INSTANCES and\n"
 "  includes four `optional` markers, which are not rules awaiting implementation —\n"
 "  c-coverage-counts-optional-as-unimplemented. None of the eight watchers; the PostToolUse\n"
 "  hook exists but does one job, refreshing the memory mirror.\n",
 "  checker's coverage line now reads 61 of 62: `optional` markers were being counted in the\n"
 "  denominator as rules awaiting implementation, which understated the checker by four and had\n"
 "  four documents repeating 'seven declared tests unimplemented' for days. None of the eight\n"
 "  watchers; the PostToolUse hook exists but does one job, refreshing the memory mirror.\n"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"  ok  {rel}")

# retire the concern (the milestone line at 427 is append-only and stays as written)
c = pathlib.Path("docs/CONCERNS.yaml")
t = c.read_text(encoding="utf-8")
start = t.index("  - id: c-coverage-counts-optional-as-unimplemented")
end = t.index("  - id: c-readme-sample-output-is-a-copy")
t = t[:start] + t[end:]
retired = '''retired_ids:
  - id: c-coverage-counts-optional-as-unimplemented
    retired: "2026-09-10"
    how: settled
    outcome: "fixed in scripts/rite-check.py — MARKER_RULES is excluded from the denominator"
    why: >
      Opened and fixed the same day, and it needed no decision: `optional` is a marker meaning
      the artifact is not required, handled by its own branch and deliberately absent from RULES.
      Counting it as an unimplemented rule understated the checker by four instances. Coverage
      now reads 61 of 62, and the one genuinely missing rule is deleted_ids_appear_in_milestones.
      Recorded as settled rather than dropped because the DOCUMENTS were the damage: four of them
      repeated "seven declared tests unimplemented" for days, reading that line as a to-do list
      it never was. A metric wrong in the flattering direction gets fixed; one wrong in the
      modest direction just quietly misinforms, which is why a low-severity counter bug was
      worth an entry at all.
      NOTE: the milestones entry for port-mirror-memory says "from 57 of 64 to 61 of 66". It is
      append-only and stays as written — it was true under the old denominator.

'''
c.write_text(t.replace("retired_ids:\n", retired, 1), encoding="utf-8", newline="\n")
print("  ok  concern retired")
