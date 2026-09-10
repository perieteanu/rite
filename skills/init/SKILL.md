---
name: init
description: Seed a project so it opens on green — writes .rite.yaml, LOG.md and HANDOFF.md at stage `idea`. Never overwrites; safe to re-run.
argument-hint: "(none = this project) | <path> = another project | --name=<short> = override the LOG short name"
disable-model-invocation: true
---

Seed a project with the files stage `idea` requires, so adopting Rite does not begin with a
screen of RED.

## Run it

```bash
python scripts/rite_init.py [PROJECT_DIR] [--name=<short>]
```

From an installed plugin the script lives under the plugin's own directory; run it from the
project root with no arguments and it seeds the current directory.

Then show the output as it came back, and run `/rite:preflight` so the user sees where the
project actually stands.

## What it writes, and what it will not

Three files: `.rite.yaml` (marker, `stage: idea`), `LOG.md` (one real entry), `HANDOFF.md`
(`genre: none`).

**Nothing else, deliberately.** `idea` is the only stage whose requirements a machine can
satisfy honestly. A log with one true entry is a complete log; a `genre: none` handoff is a
complete handoff — the standard calls it a real answer, the assertion that none is needed, made
by someone who considered the question. A seeded MISSION.md is not in that category: nobody
wrote it, it passes `file_present`, and the `populated` tests cannot tell a filled template from
an unfilled one. Seeding prose would manufacture the confidently-wrong document this project
exists to attack, at the moment of first contact.

If the user asks for more to be scaffolded, say that plainly rather than generating placeholder
documents. The honest next step is to raise `stage` and let the checker name what it wants.

## Rules

- **Never overwrite.** The script refuses, and you must not "helpfully" replace a file it
  skipped. Re-running after raising the stage is the intended use.
- **The seeded content is real, not placeholder.** Tell the user to read both files and agree
  with what they say — particularly the handoff, which asserts that nothing needs handing off.
- **Do not run it unasked.** Adopting a standard is the user's decision; this command is how
  they act on it, not how they discover it.
- **Do not install anything, and do not touch `~/.claude`.** If something is missing, report the
  gap and let the user close it — see `d-never-instruct-installation`.

## Afterwards

The project is at `idea` and green. Advancing is a human act: raise `stage` in `.rite.yaml` when
the project genuinely changes, and `/rite:preflight` will name exactly which documents are now
required. Nothing expires and nothing nags.
