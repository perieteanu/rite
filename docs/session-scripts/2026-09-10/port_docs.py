import pathlib, sys
edits = [
("docs/ROADMAP.yaml",
 "  STILL MISSING: ONE declared rule is unimplemented, deleted_ids_appear_in_milestones.",
 "  THE SESSION POST IS PORTED. scripts/rite_preflight.py is Rite's engine — eleven checks, config\n"
 "  at ${CLAUDE_PLUGIN_DATA}/checks.yaml, and a `command:` form so a check too personal to publish\n"
 "  runs an external program instead of living in the engine. SessionStart emits ONE verdict\n"
 "  covering the POST and the project standard, with a ported dedup that Rite's own hook never had.\n"
 "  Costin's preflight still runs beside it, as the mirror does; retiring it is his call.\n"
 "  STILL MISSING: ONE declared rule is unimplemented, deleted_ids_appear_in_milestones."),
("CLAUDE.md",
 "- **No port of `preflight.py` or `hookdedup.py`**, and no `checks.yaml` — `port-preflight` has\n"
 "  not started. `claude-mirror-memory.py` IS ported, as `scripts/rite_copy.py`, alongside plan\n"
 "  and session-script copying; the global hook in `~/.claude/settings.json` is deliberately\n"
 "  still running beside it until the port is proven.\n",
 "- **Both ports are done.** `claude-mirror-memory.py` is `scripts/rite_copy.py`; `preflight.py`\n"
 "  and `hookdedup.py` are `scripts/rite_preflight.py` and `scripts/ritededup.py`, with config at\n"
 "  `${CLAUDE_PLUGIN_DATA}/checks.yaml`. Costin's originals deliberately keep running beside\n"
 "  both until the ports are proven, and a parity gate guards each pair. **Do not restore\n"
 "  `mirror_drift`, `last_log_age` or `tracker_registered`** — each is superseded or out of\n"
 "  scope, with the reason recorded beside the registry.\n"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"  ok  {rel}")
