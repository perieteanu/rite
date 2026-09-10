import pathlib, sys
edits = [
("README.md",
 "- **Seven of the standard's declared tests are unimplemented**, and the report says so on every\n  run instead of quietly scoring what it can.\n",
 "- **One of the standard's declared rules is unimplemented** — `deleted_ids_appear_in_milestones`\n"
 "  — and the report says so on every run instead of quietly scoring what it can. The coverage\n"
 "  line reads `61 of 66` because its denominator counts test INSTANCES and includes four\n"
 "  `optional` markers, which are not rules awaiting implementation\n"
 "  (`c-coverage-counts-optional-as-unimplemented`).\n"),
("CLAUDE.md",
 "  `.github/workflows/gates.yml`\n  fires on every push. `test-riteyaml.py` skips there (PyYAML is its oracle and CI does not\n  install it) and `test-installed-current.py` always skips (a runner has no installed plugin).\n  The runner reports that coverage instead of showing an unqualified green — a skip is never\n  folded into a pass. It runs on **ubuntu, macos and windows** with `fail-fast: false`.\n",
 "  `.github/workflows/gates.yml` fires on every push. WHICH gates skip on a runner is declared\n"
 "  per gate as `skip_means`, and is not enumerated here for the same reason the count is not.\n"
 "  The runner reports that coverage instead of showing an unqualified green — a skip is never\n"
 "  folded into a pass. It runs on **ubuntu, macos and windows** with `fail-fast: false`.\n"),
("CLAUDE.md",
 "- **Seven declared tests unimplemented**, of which `mirror_not_stale` and\n  `source_plans_all_copied` are the ones that matter.\n",
 "- **One declared rule unimplemented**: `deleted_ids_appear_in_milestones`. This bullet said\n"
 "  \"seven ... of which mirror_not_stale and source_plans_all_copied are the ones that matter\";\n"
 "  both of those were implemented on 2026-09-10 with the copier port.\n"),
("docs/ROADMAP.yaml",
 "  STILL MISSING: seven declared tests unimplemented, now led by mirror_not_stale and\n  source_plans_all_copied. None of the eight watchers — the PostToolUse hook exists but does\n  one job, refreshing the memory mirror.\n",
 "  STILL MISSING: ONE declared rule is unimplemented, deleted_ids_appear_in_milestones. The\n"
 "  checker's coverage line reads 61 of 66 because its denominator counts test INSTANCES and\n"
 "  includes four `optional` markers, which are not rules awaiting implementation —\n"
 "  c-coverage-counts-optional-as-unimplemented. None of the eight watchers; the PostToolUse\n"
 "  hook exists but does one job, refreshing the memory mirror.\n"),
("docs/ROADMAP.yaml",
 "  Rite is an installed, running plugin at version 0.15.0 — rite@rite, six skills reachable as\n",
 "  Rite is an installed, running plugin at version 0.16.0 — rite@rite, six skills reachable as\n"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}\n  {old[:70]}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"{rel} corrected")
