---
genre: none
written: "{{DATE_ISO}}"
expires: "{{EXPIRES}}"
status: live
session_end: none
---

# HANDOFF — {{SHORT_NAME}}

There is nothing to hand off yet. The project has just adopted Rite and no session has done
work in it.

This file is **not** a placeholder waiting to be filled. `genre: none` is a real answer and it
passes: it is the assertion that no handoff is needed, made by someone who considered the
question. A handoff saying "nothing to hand off" and a missing handoff look identical from the
next session's side, except that one proves somebody decided and the other proves nothing.

## What replaces this

At the end of a real session, `/rite:end` decides the outcome and `/rite:handoff` writes the
result. HANDOFF.md is **write-once** — a change means a NEW file replacing this one, never an
edit to it — and every session ends having recorded one of four outcomes in the front matter
above: `written`, `updated`, `carried_forward`, or `none`.

Whatever replaces this must say what the documents do not. State is owned by
`docs/ROADMAP.yaml`; a handoff that restates it is duplication with a second place to go stale.

`expires` is always a date, and an expired or spent handoff fails loudly and names itself rather
than being quietly ignored — a spent handoff is worse than no handoff, because it is
confidently wrong.
