import pathlib, sys
p = pathlib.Path("skills/end/SKILL.md")
t = p.read_text(encoding="utf-8")
old = """6. Run the checks before declaring the session closed. At minimum
   `bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" check` — or `rite.ps1` on Windows without
   Git Bash — plus whatever gates the project declares. Report the result; do not claim
   done without it.
"""
new = """6. **Bring in what was written outside the project**, then say what came in:

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" copy --all
   ```

   Memory mirror, plan copies, and this session's scratchpad scripts. **The scripts are the
   urgent one** — plans and memory live under `~/.claude` and survive, while the scratchpad is
   under `/tmp` and does not survive a reboot, so the scripts that performed this session's
   edits are gone if nobody copies them.

   SessionEnd runs the same three automatically, so this step is belt and braces rather than
   the only chance. Run it here anyway: SessionEnd has no turns left and cannot tell you what
   it did, and a plan reported `UNATTRIBUTED` is something you can still act on now.

7. Run the checks before declaring the session closed. At minimum
   `bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" check` — or `rite.ps1` on Windows without
   Git Bash — plus whatever gates the project declares. Report the result; do not claim
   done without it.
"""
if t.count(old) != 1:
    sys.exit(f"ABORT: matched {t.count(old)}")
b = len(t.encode("utf-8"))
p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print(f"skills/end/SKILL.md: {b} -> {len(p.read_bytes())}")
