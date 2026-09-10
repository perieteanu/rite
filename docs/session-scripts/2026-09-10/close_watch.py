import pathlib, sys

# gate
g = pathlib.Path(".github/gates.yaml")
t = g.read_text(encoding="utf-8")
a = "  - id: copy-attribution"
new = '''  - id: watch-discipline
    command: [scripts/test-watch-discipline.py]
    what: "the write-discipline watcher catches rewrites and future timestamps, and is silent otherwise"
    # Silence on success is as load-bearing as the catching: it fires on every Write and Edit,
    # and a watcher that speaks when nothing is wrong is one the user disables within a day.

  - id: copy-attribution'''
if t.count(a) != 1:
    sys.exit("ABORT gate")
g.write_text(t.replace(a, new, 1), encoding="utf-8", newline="\n")
print("  ok  gate")

# concern retired
c = pathlib.Path("docs/CONCERNS.yaml")
t = c.read_text(encoding="utf-8")
start = t.index("  - id: c-log-timestamps-must-be-machine-read")
end = t.index("  - id: c-status-line-presence")
t = t[:start] + t[end:]
retired = '''retired_ids:
  - id: c-log-timestamps-must-be-machine-read
    retired: "2026-09-10"
    how: settled
    outcome: d-write-discipline-watcher
    why: >
      Open since 2026-09-08 with, in its own words, nowhere for its check to run. It now runs in
      two places from one predicate: as the `no_future_timestamps` rule at session start, and in
      the PostToolUse watcher the instant a write lands.
      The check is NARROWER than the concern's title and deliberately so. An invented timestamp
      in the PAST is indistinguishable from a machine-read one afterwards; nothing can catch it.
      What is provable is a timestamp in the FUTURE — and that is precisely what extrapolation
      produces when it overshoots, which is what happened on 2026-09-07: thirty entries
      extrapolated from a single 22:11 reading, some ahead of real time, found only when the
      clock was re-read at 00:02 against entries claiming 00:13.
      The concern also proposed comparing against the file's own mtime. Rejected as weaker: at
      PostToolUse the file was just written, so its mtime IS now, and `now` needs no filesystem
      round-trip and no assumption that mtime survived a copy.
      The do_not stands and was honoured: the existing entries are append-only and were not
      backfilled.

'''
c.write_text(t.replace("retired_ids:\n", retired, 1), encoding="utf-8", newline="\n")
print("  ok  concern retired")

# roadmap item closed
r = pathlib.Path("docs/ROADMAP.yaml")
t = r.read_text(encoding="utf-8")
start = t.index("  - id: watcher-write-discipline")
end = t.index("  - id: watcher-precompact-distiller")
if "PostToolUse watcher on Write|Edit" not in t[start:end]:
    sys.exit("ABORT wrong span")
t = t[:start] + t[end:]
milestone = '''  - id: watcher-write-discipline
    what: "The first of the eight watchers: append-only rewrites and future timestamps reported as they happen"
    closed: "2026-09-10"
    log_ref: "10-09-2026"
    note: >
      Chosen first of the eight because it is the only one with a MEASURED hit rate rather than
      a plausible rationale — 100% on this project's own real failures, which is what the item
      already recorded.
      It closes the gap the protocol's honest_limits named: every implemented completion test is
      an end-of-session test, so a session could rewrite an append-only file at 14:00 and the
      standard stayed green until it closed. /rite:update made the record correctable on demand;
      this makes one class of damage report itself.
      IT ALSO ABSORBED c-log-timestamps-must-be-machine-read, open since 2026-09-08 with nowhere
      for its check to run. Two items, one build, one predicate — riterules.log_future_timestamps
      is shared by the watcher and by the new no_future_timestamps rule, because two copies would
      be free to disagree about what "future" means.
      scripts/riterules.py was extracted to make that sharing possible: git_show, zone_of and
      git_removed_lines moved out of rite-check.py unchanged, so the watcher measures
      append-only violations with the same predicate the checker does.
      SILENCE ON SUCCESS IS A CONTRACT, not politeness. It fires on every Write and Edit, and a
      watcher that speaks when nothing is wrong is one the user disables within a day.

'''
anchor = "near_term:\n"
r.write_text(t.replace(anchor, milestone + anchor, 1), encoding="utf-8", newline="\n")
print("  ok  roadmap closed")
