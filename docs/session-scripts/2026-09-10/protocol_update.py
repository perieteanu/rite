import pathlib, sys
p = pathlib.Path("spec/session-protocol.yaml")
t = p.read_text(encoding="utf-8")

# 1 — runs_as reflects that two of three steps now have machinery
old_runs = '''  - id: during
    label: "During the session"
    runs_as: "PostToolUse hook -> script, plus the agent's own discipline"
    steps:
'''
new_runs = '''  - id: during
    label: "During the session"
    runs_as: >
      PostToolUse hook -> script (mirror_memory), the /rite:update command (checkpoint), and the
      agent's own discipline (log_continuously, clock_per_entry). Until 2026-09-10 it was
      discipline alone, and honest_limits said so.
    steps:
'''
if t.count(old_runs) != 1:
    sys.exit("ABORT: during header")
t = t.replace(old_runs, new_runs, 1)

# 2 — the new step
old_tail = '''        check: "no LOG entry may carry a timestamp later than the file's own mtime"
        tracked_as: c-log-timestamps-must-be-machine-read

  - id: end_judgement'''
new_tail = '''        check: "no LOG entry may carry a timestamp later than the file's own mtime"
        tracked_as: c-log-timestamps-must-be-machine-read

      - id: checkpoint
        what: "Bring the docs back to true mid-session, on demand, WITHOUT ending the session."
        runs_as: "/rite:update -> a Markdown prompt Claude interprets"
        added: "2026-09-10"
        why: >
          Measured on the session that proposed it: ROADMAP.current_state read "Stage `build` ...
          version 0.8.1" for HOURS while the repository was public and the plugin eleven versions
          on. /rite:end caught it at the close; nothing could have caught it sooner, because
          every implemented completion test is an end-of-session test. A long session is not one
          event, and treating it as one is what lets a document stay false all afternoon.
        takes: >
          The end phase's steps that are about the RECORD — distil the log, bring the docs back
          to true, close any item that actually finished, copy what was written outside the
          project, run the checks.
        deliberately_omits: >
          The handoff decision and the memory write. Those are what make an ending, and a
          checkpoint that performed them would be an ending under a gentler name. Omitting them
          is what keeps /rite:end the contract.
        the_risk_it_carries: >
          /rite:end's single weakest link is that it only fires if the user types it
          (c-status-line-presence). A friendlier sibling could cannibalise it — run the easy one
          all day and never close properly. Mitigated by naming and framing only: `update` reads
          as incomplete where `end` reads as final, and the command says outright which steps it
          is not doing.
        how_it_is_verified: >
          BY THE CORRECTION /rite:end HAS TO MAKE, and by nothing else. If checkpoints kept the
          docs true, the end phase's update_what_changed finds nothing; if it rewrites
          current_state, the checkpoints lapsed. No stamp file and no new artifact — the same
          reasoning that rejected an /end stamp, and the same reasoning that lets
          did_the_last_session_close work from two files that already exist.
        reported_never_graded: >
          The end phase RECORDS how much it had to correct and does not score it. Any pass/fail
          threshold would be a guessed number, which is c-freshness-thresholds-are-guesses
          repeating itself one level up. The magnitude in LOG.md makes the pattern visible over
          weeks without inventing a limit.

  - id: end_judgement'''
if t.count(old_tail) != 1:
    sys.exit("ABORT: during tail")
t = t.replace(old_tail, new_tail, 1)

# 3 — honest_limits: the first one is now partly false
old_lim = '''  - >
    THE START HALF RUNS; THE DURING HALF DOES NOT EXIST. SessionStart fires the hook, its
    verdict reaches the model's context, and the end half is reachable as /rite:end. But the
    `during` phase has no enforcement at all: mirror_memory, log_continuously and
    clock_per_entry are disciplines an agent must remember, which is the exact category this
    project exists to abolish. They wait on the PostToolUse watcher layer.
'''
new_lim = '''  - >
    THE DURING HALF IS HALF-BUILT AS OF 2026-09-10, and this entry used to say it did not exist
    at all. mirror_memory now runs on a PostToolUse hook, and checkpoint is reachable as
    /rite:update. What remains discipline an agent must remember is log_continuously and
    clock_per_entry — the exact category this project exists to abolish, still waiting on the
    watcher layer. Two of four is progress, not completion.
'''
if t.count(old_lim) != 1:
    sys.exit("ABORT: honest_limits")
t = t.replace(old_lim, new_lim, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("protocol updated")
