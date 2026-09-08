---
name: handoff
description: Write or update HANDOFF.md — what the next session must know that the docs do not say. Write-once, freezes at session end, and always carries an expiry date.
argument-hint: "(none = decide the outcome) | none = there is nothing to hand off, say so explicitly"
disable-model-invocation: true
---

Write the handoff: what the next session needs that is not already in the docs. A handoff is
**write-once** — it freezes at session end. Before that moment it is drafted freely; after it,
a change means a new file, not an edit.

The file always exists. "Nothing to hand off" is written down as `genre: none`, not left as an
absent file — an explicit nothing and a missing file look identical from the next session's
side, except that one proves somebody decided.

## Steps

1. Decide the outcome and record it in the front matter as `session_end:`
   - `written` — a new handoff, replacing the previous one
   - `updated` — the live one rewritten to cover this session too
   - `carried_forward` — it still holds unchanged, deliberately
   - `none` — genre `none`, an explicit statement that nothing needs handing off, and why

2. Write the front matter. Every key is required:

   ```yaml
   ---
   genre: state | prompt | task_brief | none
   written: "YYYY-MM-DD"
   expires: "YYYY-MM-DD"
   status: live
   session_end: written | updated | carried_forward | none
   ---
   ```

   `expires` is **always a date.** A condition may accompany it in prose — "when the checker
   runs, or 2026-12-07, whichever comes first" — but a condition alone is not machine-readable
   and the check cannot run on it.

3. `written:` must not be older than the newest `LOG.md` entry. If it is, the session worked
   and then closed without touching the handoff — which is precisely what the next session
   start will report.

4. Write the body for someone who was not here and has no transcript. Cover: verified current
   state with the commands that verified it, what changed and why, what is settled and must
   not be re-litigated, the traps that produce plausible-but-wrong output, what to do next in
   order, and **what was deliberately not done.**

5. Include the honest limits. Anything unverified, predicted rather than tested, or known to
   be shaky belongs in the handoff — a handoff that only carries good news is worth less than
   none, because it will be believed.

6. Show the draft and **wait for the user** before writing. Accept `y` / `n` / free-text edits.

## Don't

- **Don't restate `current_state`.** `docs/ROADMAP.yaml` owns it. Reference it; adding a
  second copy creates two records that will disagree.
- **Don't leave a spent handoff in place.** A stale handoff is worse than no handoff, because
  it is confidently wrong. Replace it, or mark `status: spent`.
- **Don't edit a frozen handoff.** Replace it wholesale and record what it supersedes.
- **Don't write `expires` as a condition alone.** A date is required.
- Don't add emojis or marketing language.
