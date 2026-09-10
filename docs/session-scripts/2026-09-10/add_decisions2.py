import pathlib
p = pathlib.Path("docs/DECISIONS.yaml")
t = p.read_text(encoding="utf-8")
before = len(t.encode("utf-8"))
entry = '''
  - id: d-attribution-is-authorship-not-mention
    date: "2026-09-10"
    title: "A plan belongs to the session that WROTE it, proved from the transcript, or to nobody"
    context: >
      c-plan-attribution blocked port-mirror-memory since 2026-09-07, calling itself "the only
      genuinely hard part" and proposing mtime correlation or content inspection.
    decision: >
      Attribution reads session transcripts at ~/.claude/projects/<slug>/*.jsonl and accepts
      exactly two proofs of authorship: a Write whose input.file_path is the plan, or an
      ExitPlanMode whose input.planFilePath is. Anything else — a Bash command, prose, a path in
      tool OUTPUT — is a mention and attributes nothing. A plan with no proof is reported
      unattributable and skipped. Two sessions claiming the same plan is reported as a conflict,
      never resolved by picking one.
    rationale:
      - >
        MENTION IS NOT AUTHORSHIP, and the cost of conflating them was measured rather than
        imagined. The first implementation matched the plan's path anywhere in a transcript and
        mis-attributed FIVE of thirteen plans. The contamination was self-inflicted: the session
        building the attributor ran `ls ~/.claude/plans/`, so rite's own transcript came to
        mention every plan on the machine. The act of measuring changed what was measured.
      - >
        IT WAS CAUGHT ONLY BY DISAGREEMENT. The new numbers contradicted a shell measurement
        taken twenty minutes earlier; nothing about the wrong answer looked wrong on its own.
        That is the argument for writing a measurement down before trusting the tool that
        replaces it — and the reason the regression test uses synthetic fixtures, so it can fail
        for a reason about the code.
      - >
        REFUSE RATHER THAN GUESS, the rule riteyaml already lives by. Placing a plan by mtime
        proximity would produce an attribution indistinguishable from a correct one after the
        fact, which is worse than leaving it uncopied and saying so.
      - >
        IT MAKES watcher-plan-copy-on-create AN OPTIMISATION, not a prerequisite. That item
        exists to copy a plan at creation because attribution "is only hard retroactively".
        Retroactive attribution now works, so the watcher buys latency and nothing else.
    limits:
      - >
        ATTRIBUTION NAMES THE SESSION'S PROJECT, NOT THE PLAN'S SUBJECT, and this repo holds the
        counterexample: docs/PLAN-2026-09-07-project-standard.md is rite's founding plan, written
        from a claude-persistent session because rite did not exist yet. Transcript attribution
        says claude-persistent and the human who filed it under rite was right. An existing copy
        therefore always wins, and the copier never moves or rewrites one.
      - "Dedupe is keyed on CONTENT, not source filename: ~/.claude/plans/<name>.md is REUSED across sessions. calm-tinkering-kahan.md held this repo's publishing plan in the morning and its copier plan in the afternoon."
    chosen_by_user: true
    proposed_by: claude

  - id: d-pattern-paths-and-declared-name-shapes
    date: "2026-09-10"
    title: "An artifact with many instances declares a glob for presence and a regex for shape"
    context: >
      plan_copy declared path "docs/PLAN-YYYY-MM-DD-<slug>.md" and rite-check.py compared it with
      exists_exactly, a literal case-sensitive test. No file can be named YYYY-MM-DD, so the
      artifact was absent on every project forever and filename_matches_canonical — the test
      whose job is to check a plan copy's NAME — had never run against one.
    decision: >
      Artifacts may declare `path_pattern` (a glob) for presence and `canonical_name_pattern`
      (a regex over the repo-relative path) for shape. `path` remains the canonical display
      name. Renaming the artifact to a literal path was rejected: there are legitimately many
      plan copies per project, and one filename would be a worse lie than the silence.
    rationale:
      - "Glob hits are re-verified through ritefs.exists_exactly, because Path.glob matches case-insensitively on macOS and Windows — the same repo would otherwise give two verdicts."
      - >
        THE SECOND KEY CAME OUT OF BUILDING THE FIRST. filename_matches_canonical initially held
        the PLAN regex inside the checker. That is a hardcoded value with no human-visible home,
        and it was silently wrong for the very next artifact to declare the rule — script_copy,
        whose leaf is an arbitrary filename under a dated directory. Caught because the artifact
        went YELLOW with all 20 instances "wrong" the moment it was declared.
    chosen_by_user: true
    proposed_by: claude

  - id: d-session-scripts-are-the-fourteenth-artifact
    date: "2026-09-10"
    title: "The scratchpad scripts a session writes are archived, and the inventory goes to 14"
    context: >
      The inventory was FROZEN at 13 on 2026-09-07, a 14th requiring a decision, with
      script-produced files outside the freeze only until their producers exist. rite_copy.py is
      that producer, so the entry is due.
    decision: >
      script_copy is the 14th artifact: docs/session-scripts/<ISO date>/<name>, write_once,
      tier 3, layer local. Sources are *.py and *.sh at the root of
      /tmp/claude-<uid>/<slug>/<session>/scratchpad.
    rationale:
      - >
        THE SCRATCHPAD IS IN /tmp AND DOES NOT SURVIVE A REBOOT. The scripts that performed a
        commit's edits are the only record of HOW it was made, and today four commits came out
        of twenty such scripts. Late is the same as never, so this runs from SessionEnd as well
        as /rite:end.
      - >
        GROUPED BY DATE, unlike plan_copy which is flat. One session produced twenty files; a
        few such sessions would bury docs/ under machinery and make the documents harder to
        find, which is the opposite of what docs/ is for.
      - "Attribution is free, unlike plans: the scratchpad path already contains the project slug."
      - "Narrow on purpose about what counts. The session that built this had a README.md.bak and a shipped-probe/ tree in the same directory; neither is a script."
    chosen_by_user: true
    proposed_by: claude
'''
p.write_text(t.rstrip("\n") + "\n" + entry, encoding="utf-8", newline="\n")
print(f"DECISIONS.yaml: {before} -> {len(p.read_bytes())}")
