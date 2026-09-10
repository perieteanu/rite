import pathlib, sys

r = pathlib.Path("docs/ROADMAP.yaml")
t = r.read_text(encoding="utf-8")
old = """    - scripts/rite_copy.py
    - scripts/test-copy-attribution.py
"""
new = """    - scripts/rite_copy.py
    - scripts/rite_preflight.py
    - scripts/rite_watch.py
    - scripts/riterules.py
    - scripts/ritededup.py
    - template/checks.yaml
    - scripts/test-copy-attribution.py
    - scripts/test-preflight-port-parity.py
    - scripts/test-watch-discipline.py
"""
if t.count(old) != 1:
    sys.exit("ABORT claims")
r.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("  ok  claim surface widened")

a = pathlib.Path("docs/ARCHITECTURE.md")
t = a.read_text(encoding="utf-8")
anchor = """  test-stage-table-guard.py  No document restates the stage mapping outside a generated block.
"""
add = """  test-stage-table-guard.py  No document restates the stage mapping outside a generated block.
  rite_preflight.py  THE SESSION POST. Eleven checks across claude/project/machine, two tiers
                     (local runs automatically, full touches the network and never does). A
                     PORT of claude-preflight, with a `command:` form so a check too personal
                     to publish runs an external program instead of living here.
  ritededup.py       Suppresses the extension's double-dispatched SessionStart. Fail-open: a
                     duplicated line is cheaper than a silently missing verdict.
  riterules.py       Predicates SHARED by the checker and the watcher — git_show, zone_of,
                     git_removed_lines, log_future_timestamps. One implementation, because two
                     would be free to disagree.
  rite_watch.py      THE WATCHER. PostToolUse: an append-only file rewritten, or a LOG entry
                     dated in the future. Silent on success — it fires on every write, and a
                     watcher that speaks when nothing is wrong gets disabled.
  test-watch-discipline.py  That the watcher catches both, and stays silent otherwise.
  test-preflight-port-parity.py  The port still agrees with the engine it came from. Temporary.
"""
if t.count(anchor) != 1:
    sys.exit("ABORT arch inventory")
a.write_text(t.replace(anchor, add, 1), encoding="utf-8", newline="\n")
print("  ok  ARCHITECTURE inventory")
