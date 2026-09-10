import pathlib, sys
p = pathlib.Path("scripts/rite_preflight.py")
t = p.read_text(encoding="utf-8")

# Cut the three unported checks by function span.
for name, nxt in (("check_tracker_registered", "def check_mirror_drift"),
                  ("check_mirror_drift", "def check_last_log_age"),
                  ("check_last_log_age", "def check_thinking_level")):
    start = t.index(f"def {name}(ctx):")
    end = t.index(nxt)
    t = t[:start] + t[end:]
    print(f"  cut  {name}")

# Registry entries go with them, and the reason goes in their place.
for line in ('    ("tracker_registered", check_tracker_registered, "local"),\n',
             '    ("mirror_drift", check_mirror_drift, "local"),\n',
             '    ("last_log_age", check_last_log_age, "local"),\n'):
    if t.count(line) != 1:
        sys.exit(f"ABORT registry: {line!r} matched {t.count(line)}")
    t = t.replace(line, "", 1)

t = t.replace('''REGISTRY = [
''', '''# NOT IN THIS LIST, AND THAT IS DELIBERATE — restoring any of the three is a regression:
#   mirror_drift        superseded by Rite's mirror_not_stale, which reads the sync stamp
#                       through a predicate shared with the copier. The original compared
#                       mtimes, which this project calls mtime theatre by name.
#   last_log_age        superseded by newest_entry_within_days_of_activity.
#   tracker_registered  reads project-tracker's projects.yaml, which the engine must not know
#                       about (d-project-tracker-stays-separate). It survives as a `command:`
#                       check in the user's own checks.yaml — see run_command_check.
REGISTRY = [
''', 1)
print("  ok   registry")

p.write_text(t, encoding="utf-8", newline="\n")
print(f"rite_preflight.py: {len(p.read_bytes())} bytes")
