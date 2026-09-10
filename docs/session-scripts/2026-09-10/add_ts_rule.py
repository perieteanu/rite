import pathlib, sys

# 1 — declare it on LOG.md
s = pathlib.Path("spec/project-standard.yaml")
t = s.read_text(encoding="utf-8")
anchor = '''      - level: populated
        rule: entries_parse'''
new = '''      - level: populated
        rule: entries_parse
      - level: integrity
        rule: no_future_timestamps
        means: >
          No entry may be dated later than now. An extrapolated timestamp is indistinguishable
          from a machine-read one AFTERWARDS — except when extrapolation overshoots, which is
          the case this catches. Failed live on 2026-09-07: the clock was read once at 22:11 and
          roughly thirty further entries carried extrapolated times, some ahead of real time,
          found only when the clock was re-read at 00:02 against entries claiming 00:13.
          Integrity tier: this is a lie in the record, not a lapse.'''
if t.count(anchor) != 1:
    sys.exit(f"ABORT spec: matched {t.count(anchor)}")
s.write_text(t.replace(anchor, new, 1), encoding="utf-8", newline="\n")
print("  ok  declared on LOG.md")

# 2 — implement it
c = pathlib.Path("scripts/rite-check.py")
t = c.read_text(encoding="utf-8")
anchor2 = '@rule("newest_entry_within_days_of_activity")'
rule = '''@rule("no_future_timestamps")
def _no_future_timestamps(ctx, art, test):
    """A dated entry later than now. See riterules.log_future_timestamps for the reasoning.

    Shares its predicate with the PostToolUse watcher, which asks the same question the instant
    a write lands. One implementation, two consumers — two copies would be free to disagree
    about what "future" means, which is the drift this project attacks everywhere else.
    """
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    future = riterules.log_future_timestamps(text)
    if future:
        return RED, (f"{len(future)} entry/entries dated in the future — a timestamp that was "
                     f"extrapolated, not read. First: {future[0]}")
    return GREEN, "no entry is dated later than now"


@rule("newest_entry_within_days_of_activity")'''
if t.count(anchor2) != 1:
    sys.exit("ABORT checker")
c.write_text(t.replace(anchor2, rule, 1), encoding="utf-8", newline="\n")
print("  ok  rule implemented")
