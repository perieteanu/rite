import pathlib, sys
p = pathlib.Path("docs/ROADMAP.yaml")
t = p.read_text(encoding="utf-8")

# 1 — the claim surface gains today's files
old_claims = """  present:
    - .github/workflows/gates.yml
    - .github/gates.yaml
    - .github/run-gates.py
    - .git
    - LICENSE
    - scripts/rite-check.py
    - hooks/hooks.json
    - skills/end/SKILL.md
    - .claude-plugin/plugin.json
"""
new_claims = """  present:
    - .github/workflows/gates.yml
    - .github/gates.yaml
    - .github/run-gates.py
    - .git
    - LICENSE
    - scripts/rite-check.py
    - scripts/rite_copy.py
    - scripts/test-copy-attribution.py
    - scripts/test-mirror-port-parity.py
    - scripts/test-stage-table-guard.py
    - docs/session-scripts
    - hooks/hooks.json
    - hooks/rite.ps1
    - skills/end/SKILL.md
    - .claude-plugin/plugin.json
"""
if t.count(old_claims) != 1:
    sys.exit("ABORT: claims block")
t = t.replace(old_claims, new_claims, 1)

# 2 — the opening two lines were stale: published today, and eleven versions behind
old_head = """  Stage `build`, declared in .rite.yaml. Verified against the filesystem, the harness and
  three operating systems on 2026-09-10.
  Rite is an installed, running plugin at version 0.8.1 — rite@rite, five skills reachable as
"""
new_head = """  Stage `shipped`, declared in .rite.yaml. Verified against the filesystem, the harness and
  three operating systems on 2026-09-10.
  NOTE WHAT THIS PARAGRAPH SAID AN HOUR AGO, because it is the standing example and it earned
  the label again: "Stage `build` ... version 0.8.1", written above a repository that had been
  public for two hours and a plugin eleven versions further on. The claims block below passed
  GREEN throughout — it checks PATHS, not values — which is its declared limit doing exactly
  what it says on the tin.
  Rite is an installed, running plugin at version 0.12.0 — rite@rite, five skills reachable as
"""
if t.count(old_head) != 1:
    sys.exit("ABORT: head")
t = t.replace(old_head, new_head, 1)

# 3 — the second half of today
anchor = "  STILL TRUE AND WORTH SAYING PLAINLY: no one but this machine has run Rite."
addition = """  THE COPIERS ARE WIRED IN, not merely written. /rite:end copies; SessionEnd calls all three
  in-process, so the subprocess into ~/.claude is gone and with it a plugin hook's dependency on
  a file only one machine has; and a PostToolUse hook refreshes the mirror when a memory file is
  written, gated on the path because a full refresh is ~66ms and PostToolUse fires on every edit.
  THE GLOBAL claude-mirror-memory HOOKS ARE RETIRED — three entries removed from
  ~/.claude/settings.json. Both halves were replaced BEFORE removal and each replacement was
  checked: SessionStart --check is now mirror_not_stale inside rite's own verdict, which names
  when the memory changed and what to run where the old line said STALE; PostToolUse is now
  rite's own. The SCRIPT is kept deliberately as Costin's fallback while rite is on trial, so two
  implementations of one output are alive at once and scripts/test-mirror-port-parity.py is the
  gate that stops them drifting. That gate is TEMPORARY BY CONSTRUCTION and says so: when the
  fallback goes it skips forever and must be deleted.
  PostToolUse was documented as DELIBERATELY ABSENT on two grounds — it would call a script only
  this machine has, and it would double-fire against settings.json. Both became false in the same
  commit, so the paragraph was rewritten rather than the hook added against a standing objection.
  STILL TRUE AND WORTH SAYING PLAINLY: no one but this machine has run Rite."""
if t.count(anchor) != 1:
    sys.exit("ABORT: anchor")
t = t.replace(anchor, addition, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("current_state and claims updated")
