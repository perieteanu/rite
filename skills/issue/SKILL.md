---
name: issue
description: Record something Rite got wrong, from whatever project you hit it in. Appends to a plugin-level feedback file, never to the project you are in — the note is about Rite, not about your work.
disable-model-invocation: true
---

Record something **Rite** got wrong.

Use it the moment it happens, from whatever project you are in. The note is about the tool, not
about your work, so it does not go in that project's `LOG.md` or `CONCERNS.yaml` — those belong
to the project.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" issue "<what happened>"
```

On Windows without Git Bash, `pwsh "${CLAUDE_PLUGIN_ROOT}/hooks/rite.ps1" issue "<...>"`.

## Steps

1. Take the user's words as the note. **Do not improve them.** The value of this file is that it
   records what irritated a real person in the moment; a tidied version records what you thought
   they meant.
2. If they gave no text, ask for one line. Do not invent one from context.
3. Run the command and report where it landed.
4. **Say nothing else.** No diagnosis, no fix, no "that's because…". If the fix is obvious, it
   will still be obvious later, and the whole point of writing it down is that now is the wrong
   time to act on it.

## Reading them back

```bash
bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" issue --list
```

Harvesting into rite's `docs/CONCERNS.yaml` is a **separate, deliberate act** — done in rite,
with the whole list in view, when someone has decided to work on Rite itself.

## Don't

- **Don't fix the thing.** Especially not mid-session in someone else's project. A tool that
  rewrites itself the instant it annoys you is a tool nobody can evaluate, because the thing
  being measured keeps moving.
- **Don't triage.** No severity, no id, no category. Those are judgements, and a judgement made
  while irritated is worse than one made later with everything in front of you.
- **Don't write it into the current project.** It is not that project's concern.
- **Don't rewrite an existing note.** The file is append-only.
