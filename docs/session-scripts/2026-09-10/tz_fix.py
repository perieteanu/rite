import pathlib, sys

# 1 — scope the rule
s = pathlib.Path("spec/project-standard.yaml")
t = s.read_text(encoding="utf-8")
old = '''      - level: integrity
        rule: no_future_timestamps
        means: >'''
new = '''      - level: integrity
        rule: no_future_timestamps
        scope: local_clock
        why_scoped: >
          LOG timestamps carry NO TIMEZONE — the format is DD-MM-YYYY HH:MM:SS and nothing else
          — so "is this dated in the future" is only answerable on a machine sharing the
          writer's clock. CI proved it on the very first push: every runner is UTC, this machine
          is UTC+3, and 67 perfectly honest entries read as future because their naive local
          times sat ahead of the runner's naive UTC wall clock. The entries were fine; the
          comparison was meaningless off-machine.
          So the check runs at SessionStart and in the PostToolUse watcher, where the reader's
          clock IS the writer's clock, and CI excludes it by scope — reported as NA naming the
          exclusion, never silently dropped.
          Widening the tolerance to cover a timezone offset was rejected: ±14 hours would make
          the check unable to catch the thing it exists for.
        means: >'''
if t.count(old) != 1:
    sys.exit("ABORT spec")
s.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("  ok  scoped local_clock")

# 2 — CI excludes it
g = pathlib.Path(".github/gates.yaml")
t = g.read_text(encoding="utf-8")
old_cmd = "    command: [scripts/rite-check.py, --exclude-scope=session]"
new_cmd = "    command: [scripts/rite-check.py, --exclude-scope=session, --exclude-scope=local_clock]"
if t.count(old_cmd) != 1:
    sys.exit("ABORT gate cmd")
t = t.replace(old_cmd, new_cmd, 1)
old_note = "    # session-scoped tests are excluded HERE and nowhere else."
new_note = '''    # local_clock is excluded for a different reason than session, and both are reported as NA
    # rather than dropped. LOG timestamps carry no timezone, so "dated in the future" is only
    # answerable on the machine that wrote them: every runner is UTC and this machine is UTC+3,
    # which made 67 honest entries read as future on the first push. See why_scoped in the spec.
    #
    # session-scoped tests are excluded HERE and nowhere else.'''
if t.count(old_note) != 1:
    sys.exit("ABORT gate note")
g.write_text(t.replace(old_note, new_note, 1), encoding="utf-8", newline="\n")
print("  ok  CI excludes it")
