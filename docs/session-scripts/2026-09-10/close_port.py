import pathlib, sys

# 1 — the concern the hook-shape gate forced
c = pathlib.Path("docs/CONCERNS.yaml")
t = c.read_text(encoding="utf-8")
anchor = "  - id: c-coverage-counts-optional-as-unimplemented"
new = '''  - id: c-session-post-is-gated-by-participation
    title: "The machine/agent POST is silent in a project that has not opted in — should it be?"
    status: open
    severity: medium
    opened: "2026-09-10"
    what: >
      `participation` says Rite prints nothing without a .rite.yaml marker. That now covers the
      session POST too, so a disk filling up or a second interactive session goes unreported in
      any directory that has not opted in — which is most of them.
    how_it_surfaced: >
      The port briefly ran the POST regardless of the marker, on the reasoning that a machine
      fact is true whether or not this directory opted in. The hook-shape gate rejected it
      within the minute, and the gate was right: quietly carving an exception into a settled
      rule is how the rule stops being one. Reverted, and raised here instead.
    the_argument_each_way: >
      FOR exempting it: the POST reports on the machine and the agent, not on the project. Opt-in
      is a promise not to judge someone's REPOSITORY, and a full disk is not a judgement about
      their repository. Costin's preflight has run everywhere for months and that is the
      behaviour he is used to.
      AGAINST: "silent where not invited" is the whole of participation, and a user who declined
      Rite did not decline it selectively. An exception also needs a rule for WHICH checks are
      exempt, and `side: machine` is a per-check declaration a user's own config can set — so
      the exemption would be user-controllable, which is worse.
    why_it_is_not_urgent: >
      Costin's own preflight hook still runs beside the port and covers every directory, so
      nothing is lost today. It becomes real when he retires it.
    do_not: "Resolve it by editing the hook. It is a DECISIONS entry either way."

'''
if t.count(anchor) != 1:
    sys.exit("ABORT concern")
c.write_text(t.replace(anchor, new + anchor, 1), encoding="utf-8", newline="\n")
print("  ok  concern opened")

# 2 — the decision
d = pathlib.Path("docs/DECISIONS.yaml")
entry = '''
  - id: d-preflight-ported-engine-and-command-checks
    date: "2026-09-10"
    title: "The session POST is Rite's engine; personal checks live in config as `command:` entries"
    context: >
      d-preflight-is-config-not-fork settled the shape on 2026-09-07 and waited three days:
      "Rite is the upstream engine. Costin's preflight shrinks to his own checks.yaml plus
      checks too personal to publish."
    decision: >
      scripts/rite_preflight.py is a PORT of preflight.py — check bodies carried verbatim where
      behaviour is unchanged. It ships ELEVEN checks. Config lives at
      ${CLAUDE_PLUGIN_DATA}/checks.yaml and is not a project artifact. A check whose config
      carries `command:` runs an external program, its exit code mapping 0/1/2/3 to
      GREEN/YELLOW/RED/NA. SessionStart emits ONE verdict covering the POST and the project
      standard, guarded by a ported dedup.
    rationale:
      - >
        A PORT, NOT A REIMPLEMENTATION. 748 lines proven over months are worth more than tidier
        code, so the transformation was surgical: swap the parser, name every encoding, guard
        the platform-specific bits, drop what is superseded. Parity is a gate, not a claim.
      - >
        `command:` IS WHAT MAKES THE 2026-09-07 DECISION EXECUTABLE. Without it, tracker_registered
        forces project-tracker's file format into the published engine, which
        d-project-tracker-stays-separate forbids. With it, anything too personal to publish
        lives in the user's config and the engine never learns about it. It is also the only
        extension point a stranger gets.
      - >
        THREE CHECKS ARE NOT PORTED, and restoring them is a regression: mirror_drift is
        superseded by mirror_not_stale, which reads a sync stamp through a predicate shared with
        the copier rather than comparing mtimes; last_log_age by
        newest_entry_within_days_of_activity; tracker_registered belongs in config.
      - >
        ONE VERDICT, NOT TWO. Costin has had one line from preflight and one from Rite,
        describing one session. The port folds them, and carries hookdedup — which guarded only
        the two hooks in settings.json and never covered Rite's own.
    corrections_forced_during_the_work:
      - "The AST gate caught a subprocess.run arriving without encoding/errors. The port was written against a rule the original predates, and the rule did its job."
      - >
        The POST was briefly made to run regardless of the .rite.yaml marker. The hook-shape gate
        rejected it inside a minute and the gate was right — `participation` is not negotiable by
        a port. Reverted and raised as c-session-post-is-gated-by-participation.
      - "Cutting the three unported checks by span also removed a helper that a KEPT check used. The engine still ran: the per-check exception guard reported it as a YELLOW naming the missing name, which is exactly the failure mode that guard exists for."
    chosen_by_user: true
    proposed_by: claude
'''
d.write_text(d.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry, encoding="utf-8", newline="\n")
print("  ok  decision appended")

# 3 — close the roadmap item
r = pathlib.Path("docs/ROADMAP.yaml")
t = r.read_text(encoding="utf-8")
old_item = '''  - id: port-preflight
    what: "Port preflight.py into Rite as the engine; reduce ~/projects/claude-preflight to a checks.yaml"
    why: "744 proven lines. The generalisation is mostly done — the machine-specific checks are already toggles."
'''
if t.count(old_item) != 1:
    sys.exit("ABORT roadmap item")
t = t.replace(old_item, "", 1)
milestone = '''  - id: port-preflight
    what: "The session POST becomes Rite's engine; preflight becomes a config, with `command:` checks for the personal ones"
    closed: "2026-09-10"
    log_ref: "10-09-2026"
    note: >
      d-preflight-is-config-not-fork settled the shape on 2026-09-07 and it waited three days.
      A PORT, not a reimplementation: check bodies carried verbatim, the transformation surgical
      — swap PyYAML for riteyaml, name every encoding, guard /proc and df, drop what is
      superseded. Eleven checks ship; three do not, and each has a reason recorded beside the
      registry so a later session does not restore them as omissions.
      THE ONE PLAUSIBLE BLOCKER WAS GONE BEFORE STARTING: riteyaml already parsed the real
      checks.yaml identically to PyYAML, verified with PyYAML as oracle. And 748 lines contained
      exactly THREE machine-specific literals, so the decision's claim that the generalisation
      had happened accidentally held up.
      `command:` checks are what make the 2026-09-07 decision executable rather than aspirational
      — without them tracker_registered forces project-tracker's file format into the published
      engine. Proved both ways: exit 2 gives RED with the detail line, a missing command gives
      YELLOW and no traceback.
      TWO GATES CORRECTED THE WORK WHILE IT HAPPENED. The AST rule caught a subprocess.run
      without encoding. The hook-shape gate rejected running the POST without a .rite.yaml
      marker — `participation` is not negotiable by a port — which became
      c-session-post-is-gated-by-participation rather than a quiet exception.
      Costin's preflight keeps running beside it, as the mirror does. Retiring it is his call.

'''
anchor = "near_term:\n"
if t.count(anchor) != 1:
    sys.exit("ABORT near_term")
r.write_text(t.replace(anchor, milestone + anchor, 1), encoding="utf-8", newline="\n")
print("  ok  port-preflight closed")
