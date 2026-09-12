---
name: update
description: Bring the project's record back to true mid-session, without ending it — distil the log, correct the docs, close finished items, copy what was written outside, run the checks. Explicitly NOT a session close.
disable-model-invocation: true
---

Bring the record back to true **without ending the session.**

This is the `during` phase's checkpoint. A long session is not one event, and treating it as one
is what lets a document stay false all afternoon: on 2026-09-10 `ROADMAP.current_state` read
*"Stage `build` … version 0.8.1"* for hours while the repository was public and the plugin
eleven versions on. `/rite:end` caught it at the close. Nothing could have caught it sooner,
because every implemented completion test is an end-of-session test.

Run it whenever a chunk of work lands — a commit, a decision, a finding. Several times a session
is normal and costs nothing.

**This is NOT a session close.** It deliberately omits the handoff decision and the memory write,
which are what make an ending. If you are finishing for the day, run `/rite:end` instead — this
command is not a substitute for it and will not record that the session closed.

## This project, resolved

!`bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" paths`

**Use the paths above, not the canonical ones in the steps below** — they differ on a project
that predates the standard. If the block is empty, skill shell execution is disabled here: fall
back to the canonical names and check each exists before editing it. If it says NOT
PARTICIPATING, the copy and check steps will do nothing; say so rather than reporting them done.

## Steps

1. **Distil the log.** Add what happened since the last checkpoint and is not yet written —
   findings, corrections, decisions taken in conversation. Where an entry turned out wrong,
   **append a dated correction**; never rewrite it. Read the machine clock for every entry.

2. **Bring the docs back to true.** Check each claim against the filesystem or the host, never
   against another document:
   - `docs/ROADMAP.yaml` `current_state` — it owns the project's stated state, and it is the
     one that goes stale fastest.
   - `docs/ARCHITECTURE.md` — if the shape changed, it is rewritten now, not at the next audit.
   - `docs/DECISIONS.yaml` — append anything settled since the last checkpoint.
   - `docs/CONCERNS.yaml` — open, update, or retire, using the file's declared lifecycle.
   - Any "not built yet" claim anywhere — if code landed, that claim is now false.
   - Any COUNT stated in prose. Counts rot faster than sentences and the claim surface cannot
     see them: it checks paths, not values.

   Do **not** touch `as_of` unless the file's claims were actually re-verified against the thing
   they describe. `as_of` is not an edit date.

3. **Close anything that actually finished.** Delete it from `near_term` and append one entry to
   `milestones` naming its `id`. If nothing finished, say so and move on — this is the step most
   likely to be a legitimate no-op.

4. **Bring in what was written outside the project:**

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" copy --all
   ```

   Memory mirror, plan copies, scratchpad scripts. **The scripts are the urgent one** — they live
   in `/tmp` and do not survive a reboot, so an unexpected end of session loses them.

5. **Run the checks and report the result:**

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" check
   ```

   Plus whatever gates the project declares. Do not claim the checkpoint is done without showing
   the output.

6. **Say what you corrected**, in one line, and put it in the log. That line is the whole
   verification story: `/rite:end` will later have to correct whatever the checkpoints missed,
   and comparing the two is how anyone knows whether checkpointing is working. There is no stamp
   file and no fifteenth artifact — the evidence is the size of the correction.

## Don't

- **Don't write or update `HANDOFF.md`.** That is `/rite:end`'s job and the thing that makes it
  an ending. A handoff written mid-session is a claim about a session that has not happened yet.
- **Don't write memory.** Memory is end-of-session judgement about what outlives the repo.
- **Don't treat this as the close.** If nobody runs `/rite:end`, the next session's start check
  reports that the last one never closed — and it will be right.
- **Don't skip a step because little happened.** Execute it and record the no-op. A skipped step
  and a step with nothing to do must not look alike.
- **Don't grade yourself.** Report how much you corrected; do not decide whether it was too much.
  Any threshold would be a guessed number, which is the mistake already open as
  `c-freshness-thresholds-are-guesses`.
- Don't add emojis or marketing language.
