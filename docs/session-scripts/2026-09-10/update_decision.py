import pathlib
d = pathlib.Path("docs/DECISIONS.yaml")
entry = '''
  - id: d-checkpoint-is-not-an-ending
    date: "2026-09-10"
    title: "/rite:update brings the record back to true mid-session and deliberately cannot close it"
    context: >
      The protocol has declared a `during` phase since 2026-09-08, and honest_limits said it had
      no enforcement at all — mirror_memory, log_continuously and clock_per_entry were
      disciplines an agent must remember, "the exact category this project exists to abolish".
      Measured cost on 2026-09-10: ROADMAP.current_state read "Stage `build` ... version 0.8.1"
      for hours while the repository was public and the plugin eleven versions on.
    decision: >
      A fourth `during` step, `checkpoint`, reachable as /rite:update. It takes the end phase's
      RECORD steps — distil the log, bring the docs true, close anything that finished, copy what
      was written outside, run the checks — and deliberately omits the handoff decision and the
      memory write.
    rationale:
      - >
        A LONG SESSION IS NOT ONE EVENT. Every implemented completion test is an end-of-session
        test, so a document can stay false all afternoon and the standard stays green. /rite:end
        caught current_state at the close; nothing could have caught it sooner.
      - >
        OMITTING THE HANDOFF IS WHAT KEEPS /rite:end THE CONTRACT. A checkpoint that wrote a
        handoff would be an ending under a gentler name, and /rite:end's single weakest link is
        already that it only fires if the user types it (c-status-line-presence). The mitigation
        is naming and framing: `update` reads as incomplete, and the command says outright which
        steps it is not doing.
      - >
        IT IS VERIFIED BY THE CORRECTION /rite:end HAS TO MAKE, and by nothing else. If
        checkpoints kept the docs true, update_what_changed finds little; if it rewrites
        current_state, they lapsed. No stamp file and no fifteenth artifact — the same reasoning
        that rejected an /end stamp, and that lets did_the_last_session_close work from two files
        which already exist.
      - >
        REPORTED, NEVER GRADED. /rite:end records the magnitude of its correction and does not
        score it. Any pass/fail threshold would be a guessed number, which is
        c-freshness-thresholds-are-guesses repeating itself one level up.
    also_recorded: >
      The during phase is now HALF-BUILT rather than absent: mirror_memory runs on the
      PostToolUse hook added the same day, checkpoint is /rite:update, and log_continuously and
      clock_per_entry remain discipline waiting on the watcher layer. honest_limits was corrected
      to say two of four rather than none.
    chosen_by_user: true
    proposed_by: claude
'''
d.write_text(d.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry, encoding="utf-8", newline="\n")
print("decision appended")
