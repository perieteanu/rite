import pathlib, datetime
d = pathlib.Path("docs/DECISIONS.yaml")
entry = '''
  - id: d-write-discipline-watcher
    date: "2026-09-10"
    title: "The first watcher reports append-only rewrites and future timestamps as they happen"
    context: >
      The protocol's honest_limits said every implemented completion test is an end-of-session
      test, so a session could rewrite an append-only file at 14:00 and the standard stayed green
      until it closed. Eight watchers sat in mid_term; this is the first built.
    decision: >
      scripts/rite_watch.py runs on PostToolUse for Write|Edit|MultiEdit. It reports two things
      and nothing else: an existing line changed in a file the standard declares append_only,
      measured against git HEAD; and a LOG entry dated later than now. It is SILENT otherwise
      and always exits 0.
    rationale:
      - >
        CHOSEN FIRST BECAUSE IT IS THE ONLY ONE WITH A MEASURED HIT RATE — 100% on this
        project's own real failures, as the roadmap item already recorded. The other seven rest
        on plausible rationales, and two have since lost their premise.
      - >
        SILENCE ON SUCCESS IS A CONTRACT, not politeness. It fires on every write. A watcher
        that speaks when nothing is wrong is one the user disables within a day, and a disabled
        watcher catches nothing at all.
      - >
        IT MEASURES AGAINST git HEAD, so it holds no state of its own and cannot be fooled by a
        second write to the same file. It also means the predicate is the one the checker
        already uses.
      - >
        ONE PREDICATE, TWO CONSUMERS. scripts/riterules.py was extracted so the watcher and the
        checker ask the same question the same way. Two copies of "was this rewritten?" or of
        "what counts as the future?" would be free to disagree — the drift the mirror and
        preflight parity gates exist to catch, except self-inflicted.
    absorbed: >
      c-log-timestamps-must-be-machine-read, open since 2026-09-08 with nowhere for its check to
      run. The check is NARROWER than that concern's title, deliberately: an invented timestamp
      in the PAST is indistinguishable from a real one afterwards and nothing can catch it. A
      timestamp in the FUTURE is provable, and it is exactly what extrapolation produces when it
      overshoots — which is what happened on 2026-09-07.
      The concern proposed comparing against the file's own mtime. Rejected as weaker: at
      PostToolUse the file was just written, so its mtime IS now, and `now` needs no filesystem
      round-trip and no assumption that mtime survived a copy.
    also_settled: >
      The verdicts fixture stopped pinning a literal NA count. It broke three times in one day —
      59, then 60, then nearly 61 — every time an artifact or rule was added, and every break was
      noise rather than a finding. It now asserts the invariant it always meant: every declared
      check lands in exactly one bucket, so collapsing cannot quietly drop one. Raised twice
      before as brittle; fixed while editing the same file for a third time.
    chosen_by_user: true
    proposed_by: claude
'''
d.write_text(d.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry, encoding="utf-8", newline="\n")

p = pathlib.Path("LOG.md")
entries = [
 ("add", "watcher-write-discipline BUILT — d-write-discipline-watcher, the first of the eight. PostToolUse on Write|Edit reports two things and nothing else: an existing line changed in an append-only file, measured against git HEAD, and a LOG entry dated later than now. Silent otherwise, always exits 0"),
 ("note", "Chosen first because it is the ONLY one of the eight with a measured hit rate rather than a plausible rationale — 100% on this project's own real failures, which the roadmap item already recorded. Two of the other seven have since lost their premise entirely"),
 ("fix", "It ABSORBED c-log-timestamps-must-be-machine-read, open since 2026-09-08 with nowhere for its check to run. Two items, one build. The check is narrower than that concern's title and deliberately so: an invented timestamp in the PAST is indistinguishable from a real one afterwards, but a FUTURE one is provable — and that is exactly what extrapolation produces when it overshoots, which is what happened on 2026-09-07"),
 ("add", "scripts/riterules.py extracted so the watcher and the checker share one predicate. git_show, zone_of and git_removed_lines moved out of rite-check.py unchanged, and log_future_timestamps joins them. Two copies of 'was this rewritten?' would be free to disagree — the drift the parity gates catch, except self-inflicted"),
 ("note", "SILENCE ON SUCCESS proved as carefully as the catching, because it fires on every write and a watcher that speaks when nothing is wrong gets disabled within a day. My first silence test FAILED and the code was right: I hardcoded 19:20:00 as a 'legal' entry while the clock read 19:07, so it was correctly flagged as future. Fixtures are computed from now() in the gate for exactly that reason"),
 ("fix", "The verdicts fixture stopped pinning a literal NA count. It broke three times in one day — 59, 60, nearly 61 — every time an artifact or rule was added, and every break was noise. It now asserts the invariant it always meant: every declared check lands in exactly one bucket. Raised twice as brittle and fixed on the third encounter rather than bumped again"),
]
lines = []
for kind, text in entries:
    now = datetime.datetime.now()
    dow = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][now.weekday()]
    lines.append(f"{now.strftime('%d-%m-%Y %H:%M:%S')} | {dow} | rite | [{kind}] {text}")
with p.open("a", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print(f"decision + {len(lines)} log entries")
