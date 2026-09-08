---
name: log
description: Append an entry to this project's LOG.md — the durable record that outlives the session. Reads the machine clock per entry. Append-only.
argument-hint: "(none = propose entries from what just happened) | [TYPE] free text = log exactly this"
---

Append one or more entries to `LOG.md` in the current project. The log is the durable record:
transcripts are pruned by the harness within weeks, so whatever is not written here is gone.

Log **as work happens**, not only at the end. If the session dies before `/end`, everything
written up to that point survives.

## Steps

1. **Read the machine clock. Every time. Before composing anything.**

   ```bash
   LC_ALL=C date '+%d-%m-%Y %H:%M:%S | %a'
   ```

   Use the value it returns. Do **not** extrapolate from an earlier reading, and do not
   estimate from how long the work felt. `LC_ALL=C` is required — the system locale is
   `ro_RO` and `%a` would otherwise emit `Lun` / `Jo`.

2. Determine the entry format from `docs/CONVENTIONS.md`:

   ```
   DD-MM-YYYY HH:MM[:SS] | DDD | <short_name> | [TYPE] description
   ```

   Seconds are optional but preferred — they let entries be true when several land in the
   same minute. There is **no minimum spacing**; entries carry the time they were written.
   `short_name` comes from CONVENTIONS; EU date order and English day abbreviation are both
   deliberate, for parser stability.

3. Choose the `[TYPE]` from the project's declared vocabulary — typically
   `work` `note` `fix` `decide` `pivot` `add` `defer` `drop` `done`.
   `decide` and `pivot` mean the change also belongs in `docs/DECISIONS.yaml`.

4. Write the description so it is useful to someone who was not here. State what was found or
   changed **and why it mattered**, not what was touched. A finding with its evidence beats a
   summary of activity.

5. Show the draft entries in plain text — not a code diff — and **wait for the user.**
   Accept `y` / `n` / free-text edits. Do not append before approval.

6. Append to the end of `LOG.md`. Never insert, never reorder, never edit an existing line.
   If a past entry turns out wrong, append a new `[fix]` entry correcting it and say so.

## Don't

- **Don't invent a timestamp.** An invented one is indistinguishable from a real one
  afterwards, which is what makes it corrosive. If you did not read the clock for this entry,
  you do not have its time.
- **Don't rewrite, reorder or tidy existing entries.** `LOG.md` is append-only. File order is
  insertion order and may differ from chronological order; consumers sort by timestamp.
- **Don't touch `next-steps.yaml`, `projects.yaml` or any `EVOLUTION.yaml`.** Those belong to
  project-tracker, which answers a different question.
- Don't add emojis or marketing language.
- Don't log noise. An entry nobody would read later is worse than no entry, because it
  dilutes the ones that matter.
