<!-- Copied from ~/.claude/plans/floofy-sleeping-octopus.md on 2026-09-10.
     Plans are written outside the project under harness-generated names carrying no
     project attribution; they are lost when the session ends unless copied. Canonical
     name per spec/project-standard.yaml artifact `plan_copy`. Copied by rite_copy.py,
     which attributes a plan to the project whose SESSION wrote it. -->

# The seed set: a project adopting Rite opens on green

## Context

`d-stage-gates-the-standard` had two halves. The gating landed earlier today — a day-one project
went from 9 RED to 2. This is the other half: those last 2 REDs are `LOG.md` and `HANDOFF.md`,
and today a newcomer must hand-write both, correctly, before the tool stops complaining. The
gating made the target small; the seed set is what actually reaches it.

Also folds in the publishing checklist, because `publish-github` is no longer a one-line
visibility flip: it is three things at once (visibility, `stage: shipped`, LICENSE going live)
and nothing records that.

## The scope decision, which is the whole design

**`/rite:init` scaffolds a project to stage `idea` and stops.** It does not seed MISSION,
README, ARCHITECTURE or anything else.

`idea` is the only stage whose requirements a machine can satisfy *honestly*:

- a LOG with one real entry **is** a complete log
- a HANDOFF with `genre: none` **is** a complete handoff — the spec says so in as many words:
  *"a REAL answer and it passes… the assertion that none is needed, made by someone who
  considered the question"*

Every other artifact fails that test. A seeded `MISSION.md` nobody has written is a lie that
passes `file_present`, and the `populated` tests cannot tell a filled template from an unfilled
one — enough headings and it scores. Shipping placeholder prose would manufacture exactly the
confidently-wrong document this project exists to attack, and would do it at the moment of first
contact.

So advancing past `idea` stays a human act, and the checker already names precisely which files
it wants. That is the tool being useful rather than obsequious.

## Deliverables

### 1. `template/` — three files, with substitution tokens

`.rite.yaml`, `LOG.md`, `HANDOFF.md`. Real files rather than string literals in the script,
because the seed CONTENT is config and belongs somewhere a human can read and edit it.

**They cannot be literal copies.** Both carry dates that are load-bearing:

- `LOG.md` is checked by `newest_entry_within_days_of_activity` (30) — a template with a baked
  date starts a clock the day it is committed and ships stale.
- `HANDOFF.md` is checked by `not_expired`, and `expires` must be a real date.

So the templates carry explicit tokens — `{{DATE}}`, `{{TIME}}`, `{{DOW}}`, `{{EXPIRES}}`,
`{{SHORT_NAME}}` — substituted at scaffold time from the machine clock. Note the inversion of
the usual trap: generated output must never carry a timestamp, but *scaffolded* output must, and
it has to be read at scaffold time rather than authored in.

HANDOFF's required front matter is fixed by the spec: `genre`, `written`, `expires`, `status`,
`session_end`. The seed is `genre: none`, `session_end: none`, `status: live`.

### 2. `scripts/rite_init.py` + `skills/init/SKILL.md`

Real file I/O, so it needs a script; the skill is the prompt that invokes it —
`d-plugin-components-are-mostly-prompts`.

- **Never overwrites.** An existing file is left untouched and reported as skipped. The command
  is safe to re-run, and re-running after advancing the stage is the intended use.
- **Reports what it wrote and what it skipped**, then tells the user to run `/rite:preflight`.
- Writes `newline="\n"`, `encoding="utf-8"`, and calls `ritefs.use_utf8_stdio()` — the new
  portability rules apply to it like anything else, and gate 8 will say so if it forgets.
- `short_name` derives from the directory name; the user can override with an argument.
- Does **not** touch `~/.claude`, install anything, or run git. `d-never-instruct-installation`.

### 3. `scripts/test-scaffold.py` — gate 9, and the seed set's completion test

The roadmap says each seed file must be *"the VALID SMALLEST INSTANCE: it has to pass
rite-check"*. That cannot be checked in place — `template/LOG.md` is not at a canonical path, so
the checker never looks at it. The check that means something:

> scaffold into a temp directory, run `rite-check.py` against the result, require **0 RED**.

That makes the claim testable instead of aspirational, and it fails the day a template drifts
from the standard. Add to `.github/gates.yaml`.

### 4. The publishing checklist

A `checklist:` block on `publish-github` in `docs/ROADMAP.yaml`, recording that the publishing
commit does three things together: flips visibility, sets `stage: shipped`, and thereby turns the
LICENSE check live. Plus the prerequisites already settled, so the list is complete rather than a
reminder to think.

### 5. Bookkeeping

- `template/` is **not** a 14th artifact. `d-inventory-frozen-at-13` covers what a project
  carries; this is plugin content, like `skills/`. Stated explicitly in a DECISIONS entry,
  because the freeze exists precisely to stop additions being absorbed without argument.
- One DECISIONS entry: `d-scaffold-only-what-can-be-honest`.
- `docs/ARCHITECTURE.md` gains `template/` and the new script; README's "no template/ seed set"
  sentence becomes false and must move; `current_state`; CLAUDE.md.
- Plugin version bump — a new skill and a new gate is a minor.

## Verification

1. **The headline claim.** Scaffold an empty directory, run the checker: **0 RED at stage
   `idea`**. This is gate 9 and it is the reason the work exists.
2. **Idempotent and non-destructive.** Run `/rite:init` twice; the second run writes nothing and
   says so. Then corrupt one seeded file, re-run, confirm it is *not* silently repaired.
3. **The dates are real.** Scaffold, then assert the LOG entry's date and HANDOFF's `written`
   match today's machine clock, and that `{{` appears nowhere in the output.
4. **Honest about the next stage.** Scaffold, set `stage: spec`, re-run the checker: expect 4 RED
   naming README, CLAUDE.md, MISSION, ROADMAP. The tool must state what it will not write.
5. All 9 gates green locally, then all three platforms in CI.

## Not in this plan

- No seeding beyond stage `idea`, per the scope decision above.
- Not publishing, and not advancing rite's own stage — the checklist is written, not executed.
- No `readme-for-a-stranger`; it is the next `near_term` item and wants its own pass.
