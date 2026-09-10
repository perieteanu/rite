---
name: end
description: Close the session properly — distil the log, bring the docs back to true, close finished roadmap items, and record a handoff decision. The judgement half of the session protocol.
argument-hint: "(no arguments — run this while turns remain, before you stop working)"
disable-model-invocation: true
---

Close the session. This is the **judgement half** of the protocol: it needs decisions, so it
must run while Claude still has turns. The `SessionEnd` hook fires with no turns left and can
only do mechanical work — anything requiring thought has to happen here or not at all.

Run this **every session, regardless of size.** A three-minute session has nothing to distil
and no docs whose claims moved — every step still executes and each one is a no-op with a
recorded reason. The ritual scales by content, not by exemption.

Only the user invokes this. Claude never decides that a session is over.

## Steps

1. **Distil the log.** Review the entries written during the session. Add what is missing —
   findings, corrections, decisions taken in conversation but never written down. Where an
   entry turned out to be wrong, **append a dated correction**; never rewrite it.

2. **Bring the docs back to true**, then **say how much you had to correct** — one line, into
   the log. That line is the only verification `/rite:update` has: if checkpoints kept the docs
   true this step finds little, and if it rewrites `current_state` they lapsed. Report the
   magnitude; never score it. Any pass/fail threshold would be a guessed number.

   For each, check the claim against the filesystem or the host, never against another document:
   - `docs/ROADMAP.yaml` `current_state` — it owns the project's stated state.
   - `docs/ARCHITECTURE.md` — declared must-be-current. If the shape changed this session,
     it is rewritten this session, not at the next audit.
   - `docs/DECISIONS.yaml` — append anything settled today. Never edit a past entry; append a
     dated correction block inside it.
   - `docs/CONCERNS.yaml` — open, update, or retire, using the file's declared lifecycle.
   - Any "not built yet" claim anywhere — if code landed, that claim is now false.

   Do **not** touch `as_of` unless the file's claims were actually re-verified against the
   thing they describe. `as_of` is not an edit date.

3. **Close finished roadmap items.** Delete each from `near_term` and append one entry to
   `milestones` naming its `id`. Never mark an item done in place — the roadmap states the
   future only, and `milestones` is the append-only record of what shipped.

4. **Record the handoff decision.** Exactly one of four outcomes, written into
   `HANDOFF.md` front matter as `session_end:`
   - `written` — a new handoff replaces the previous one
   - `updated` — the live one is rewritten to cover this session too
   - `carried_forward` — it still holds, unchanged, deliberately
   - `none` — genre `none`: an explicit statement that there is nothing to hand off

   "Nobody thought about it" is not one of the four, and is the failure this step exists to
   catch. Use `/handoff` for the writing itself.

5. **Write what is worth remembering**, and only that. Memory is for what the repo cannot
   hold. A decision belongs in `DECISIONS.yaml`, not in memory.

6. **Bring in what was written outside the project**, then say what came in:

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" copy --all
   ```

   Memory mirror, plan copies, and this session's scratchpad scripts. **The scripts are the
   urgent one** — plans and memory live under `~/.claude` and survive, while the scratchpad is
   under `/tmp` and does not survive a reboot, so the scripts that performed this session's
   edits are gone if nobody copies them.

   SessionEnd runs the same three automatically, so this step is belt and braces rather than
   the only chance. Run it here anyway: SessionEnd has no turns left and cannot tell you what
   it did, and a plan reported `UNATTRIBUTED` is something you can still act on now.

7. Run the checks before declaring the session closed. At minimum
   `bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" check` — or `rite.ps1` on Windows without
   Git Bash — plus whatever gates the project declares. Report the result; do not claim
   done without it.

## Don't

- **Don't skip a step because the session was small.** Execute it and record that it was a
  no-op. A skipped step and a step with nothing to do must not look alike.
- **Don't move `as_of` for a reformat, a typo, or a file conversion.** Only a real
  re-verification moves it; collapsing that turns every freshness test into mtime theatre.
- **Don't mark roadmap items done in place**, and don't rewrite an existing milestone.
- **Don't write a handoff that restates `current_state`.** ROADMAP owns it; the handoff
  references it and adds what the docs do not say.
- Don't add emojis or marketing language.
