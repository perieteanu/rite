---
genre: state
written: "2026-09-08"
session_end: updated
supersedes: "the 2026-09-08 00:02 handoff"
expires: "when the checker runs, or 2026-12-07, whichever comes first"
status: live
---

# HANDOFF — rite

**Read this, then [`CLAUDE.md`](CLAUDE.md), then [`docs/ROADMAP.yaml`](docs/ROADMAP.yaml) and
[`docs/CONCERNS.yaml`](docs/CONCERNS.yaml).**

Run this first:

```bash
cd ~/projects/rite
python3 spec/render-standard.py --check              # must print OK
python3 spec/render-standard.py --protocol --check   # must print OK
```

## State (verified 2026-09-08 14:00)

| | |
|---|---|
| artifacts in the standard | **13, FROZEN** |
| ADRs | 28 |
| concerns | 7 open, 2 retired |
| ROADMAP | 4 near_term · **12 mid_term** · 4 milestones |
| LOG entries | 112 |
| `spec/project-standard.yaml` → `.md` | 1094 → 533 (generated) |
| `spec/session-protocol.yaml` → `.md` | 237 → 129 (generated) |
| registered in `projects.yaml` | **yes** — `rite`, ai-collab, stage `spec` |

**Both halves are now written.** The project standard and the session protocol, each generated
and drift-gated by one renderer (`--check`, `--protocol --check`).

**Still no plugin code.** No `hooks/`, `commands/`, `skills/`, or scripts. Not a git repo. No
LICENSE — so rite still fails its own standard at stage `shipped`, deliberately and visibly.

## What this session did

1. **Registered rite** in project-tracker, the tracker's way — `seed-projects.py` PROJECTS list,
   not by hand-editing the generated `projects.yaml`.
2. **Wrote the session protocol** — `spec/session-protocol.yaml`. Four phases, five completion
   tests, four of them implementable today with no revision history.
3. **Accepted a third checking layer** — continuous watchers via command hooks
   (`d-continuous-watcher-layer`). Eight into mid_term, four proposals rejected into
   ARCHITECTURE.
4. **LOG timestamps gained optional seconds**, across rite, project-tracker and preflight, with
   a round-trip test.

## The four findings worth keeping

**A command hook is executed by the harness — Claude is not consulted, the user takes no
action.** That makes the continuous layer the only mechanically reliable one, and the right one
to police `/end`, which fires only if typed. This is the reframing the whole watcher idea rests on.

**On tool events, plain-text stdout goes to the debug log only** — invisible to Claude *and* the
user. A watcher must emit JSON with `additionalContext`. `additionalContext` reaches Claude,
`systemMessage` reaches the user, and `systemMessage` does nothing on this machine.

**Most of a plugin is not code.** Skills, commands and agents are Markdown prompts Claude
interprets; only scripts execute. So `/end`, `/log`, `/handoff` need no interpreter at all —
which narrows `d-python-is-the-runtime` to *Rite's scripts* need Python, not Rite.

**`seed-projects.py` rewrites every LOG.md from its own parse and silently drops unparseable
lines.** Demonstrated, not predicted: the round-trip test drops 3 of 5 sample lines on the
pre-patch parser. Any future log-format change must pass `project-tracker/test-log-roundtrip.py`.

## Do NOT re-litigate

28 ADRs. Load-bearing, in addition to yesterday's: `d-inventory-frozen-at-13`,
`d-python-is-the-runtime`, `d-stdlib-only-yaml-subset`, `d-two-shims-sh-and-ps1`,
`d-plugin-components-are-mostly-prompts`, `d-session-protocol-shape`,
`d-continuous-watcher-layer`, `d-log-seconds-optional`.

Still absolute: `d-profiling-never-integrated` — `ai-collab-profile/`, `prompts.db`,
`prompts-corpus.jsonl` are Costin's alone. Never read, ingest, derive from or ship anything
from them. A cross-transcript usage aggregate was rejected this session for having the same
*shape*, even though the ADR names only three files.

## Next, in order

1. Both gates → OK.
2. **`yaml-subset-parser`** — the first real code, and the reason to do it now is that **PyYAML
   must still be installed as the differential-test oracle**. Acceptance criteria and a
   reversal condition are already written into the roadmap item.
3. `c-unimplementable-tests` — blocks the checker; postponed twice now.
4. `checker-implementation`.
5. The watcher layer (mid_term, 8 items). Costin has said it **will** be implemented; which
   ones and in what order is not yet chosen.

## Open concerns

`c-unimplementable-tests` (**high**, blocks the checker) · `c-plan-attribution` (a closure route
now exists — copy on creation via `FileChanged`) · `c-freshness-thresholds-are-guesses` ·
`c-ai-collab-interaction-boundary` (no longer blocking; the start frame is deferred) ·
`c-standard-version-policy` · `c-log-has-no-item-ids` · `c-log-timestamps-must-be-machine-read`
(the watcher is its home)

## Honest limits

- **Nothing is implemented.** Two specs, no hooks, no commands, no scripts.
- **The 8 portability rules are still predictions.** No Windows or macOS machine has run any of this.
- **The watcher mechanics are documented, not tested.** `FileChanged` watching paths outside the
  project root, and `PreCompact` accepting a `prompt`-type hook, are both **unverified**.
- **The nag-once mechanism has an unresolved contradiction**, recorded in the protocol's
  `honest_limits`: it needs to record that a report was delivered, and the obvious place is
  HANDOFF front matter — but HANDOFF is `write_once` and freezes at session end, so a
  SessionStart write would violate its own discipline. Settle this before implementing.
- **LOG timestamps before 2026-09-08 13:56 are minute-precision, and those from 2026-09-07
  22:34 onward were extrapolated rather than read.** The correction is logged. Don't trust
  minute-level accuracy in that window.

## Raised at the very end, unsettled

`c-status-line-presence` — a **static** command-reference popup: which Rite commands exist and
how to use them. Not live data.

It solves the protocol's one unreliable link: **`/end` only fires if typed.** The harness fires
SessionStart regardless, but the judgement half depends entirely on the user knowing the command
exists. Without discoverability Rite is preflight with extra documents.

Claude was wrong twice here and both are recorded in the concern: first framing it as "should we
build a status bar" (one already exists in `claude-persistent`, 412 lines, verdict-shaped, a
pure renderer of a status file), then arguing the content should be the verdict and calling a
command list "wallpaper" — an argument that belongs to things which PUSH, not to a hover tooltip
which PULLS.

The one requirement worth holding: **generate the panel from `commands/*.md` frontmatter**, never
hand-write it. It is a document describing the product, and hand-written it becomes a lie the
first time a command is renamed — inside the tool whose argument is that unchecked docs rot.

Open: where it lives — the existing claude-persistent tooltip (reviving the viewer earlier than
`d-plugin-is-the-product` assumed) or a plugin-native `statusLine`, which is text-only and has
no hover.

## Session state

Costin left mid-session ("will continue later"). This handoff was updated rather than frozen —
if the session resumes, it can be rewritten; if it doesn't, this is accurate as of 14:00.
