---
genre: task_brief
written: "2026-09-08"
session_end: written
supersedes: "the 2026-09-08 19:04 handoff, whose single purpose — the live-session test — is complete"
expires: "2026-12-07"
status: live
---

# HANDOFF — rite

The previous handoff existed to answer one question: what does the installed plugin do inside a
live session. **Answered.** Both halves, and they went opposite ways.

- The feared failure did **not** happen: plugin skills are namespaced (`/rite:log`,
  `/rite:preflight`, `/rite:handoff`, `/rite:end`), so nothing of Costin's is shadowed.
- A failure nobody had considered **did**: the SessionStart hook had never spoken. It emitted a
  top-level `additionalContext`; the harness reads `hookSpecificOutput.additionalContext`. It
  ran, exited 0, emitted valid JSON, was logged `success`, and reached nobody.

Fixed, pinned by `scripts/test-hook-output.py`, shipped as 0.1.1. State is in
`ROADMAP.current_state`; the reasoning is `d-hook-output-shape-is-a-contract`.

## Do this first — it takes one minute and it expires

**Look at the top of your own context for a line beginning `rite — project standard:`.**

This session is the first one that can possibly show it, and the observation cannot be made
later. Three outcomes, all worth knowing:

| what you see | what it means |
|---|---|
| the line, once | the fix landed. Say so in the log; it is the completion of the 08-09 work |
| the line, **twice** | the double-dispatch reaches a single session after all. `c-installed-copy-can-be-stale` is unrelated; this reopens whether Rite needs `hookdedup`-style suppression, which was ruled unnecessary on evidence gathered on 08-09 |
| no line at all | the fix did not deploy. Check the cache version before assuming the code is wrong: `claude plugin list` against `.claude-plugin/plugin.json` |

## Two rulings Costin owes, both raised and both unanswered

Neither blocks work. Both will rot into "we always did it this way" if nobody decides.

1. **`c-installed-copy-can-be-stale`** — should the checker enforce that the installed cache
   matches the repo? It would be the first check about Rite's own delivery rather than about a
   project's documents, which may be the reason to refuse it.
2. **`c-marker-lookup-not-case-exact`** — `Path.exists()` finds the `.rite.yaml` marker in both
   `rite_session_start.py` and `rite-check.py`, while `rite-check.py` carries the case-exact
   helper written to forbid exactly that. Deliberate exemption, or the checker failing to check
   itself? Either answer is fine; silence is not.

## The trap this session actually taught

**`success` from a third-party harness means it did not crash — not that it did anything.**
The 08-09 session verified the hook by running it by hand and recorded it as working. It *was*
working, uselessly. Only a live session could tell the difference, and only because the missing
line was noticed. Prefer observing the effect over reading the report of the attempt.

Its corollary, which cost a real debugging detour: **the working tree is not what runs.** The
install cache is a real copy and `claude plugin update` is version-gated, so editing a file
changes nothing until `.claude-plugin/plugin.json` gets a new version. Bump it, or you are
testing the previous install.

## Standing traps, unchanged

- **Read the machine clock per LOG entry.** This session's entries were written by a shell loop
  calling `date` so no timestamp passed through the model at all. That is the cheapest known fix
  for `c-log-timestamps-must-be-machine-read` and it is worth keeping.
- Both `spec/*.md` are generated. Edit the `.yaml`, regenerate. Two gates.
- Closing a roadmap item means **deleting** it and **appending** a milestone.
- `as_of` moves only on real re-verification. It moved on ROADMAP this session because
  `current_state` was re-derived from the filesystem; it did **not** move on DECISIONS or
  CONCERNS, where entries were merely appended.
- Never touch `ai-collab-profile/`, `prompts.db`, `prompts-corpus.jsonl`.

## Next

`LICENSE` — rite fails its own standard at stage `shipped` without one, and the stage is the
only reason the checker says NA instead of RED. Then the three unimplemented checker rules,
then `port-mirror-memory`, which is where `PostToolUse` belongs, then the watchers.
