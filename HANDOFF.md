---
genre: task_brief
written: "2026-09-10"
session_end: written
supersedes: "the 2026-09-09 handoff, which was written before CI existed and named CI as the next move"
expires: "2026-12-09"
status: live
---

# HANDOFF — rite

State is in `ROADMAP.current_state`. This is what the docs do not say.

`near_term` holds **one item: `publish-github`**, and nothing technical is in the way. Four
items were queued and closed in a single day. The remaining act is Costin's.

## The shape of what happened, because the order matters

The previous handoff said *"CI, before scaffolding"* and that ordering paid off far beyond CI.
Each thing built exposed the next defect, in a chain:

1. **CI ran the gates** — and immediately caught that the gate count was **seven, not six**, a
   number four documents had been repeating.
2. **The matrix ran on three OSes** — macOS passed (first *evidence* that
   `case_sensitive_name_matching` works), Windows failed on a real encoding bug, which produced
   a **fourth portability rule**.
3. **That rule was violated at five of seven call sites within the hour**, found by grepping —
   which produced the AST gate that now enforces it.
4. **Stage gating** took a day-one project from 9 RED to 0.
5. **Writing an honest README example** exposed that the same change had replaced a wall of RED
   with a wall of NA — 54 lines to convey one finding.

Nothing in that chain was planned. Every link came from something *failing* where it could be
seen. That is the method working, and it is worth trusting next session over any plan.

## What to do next, and the one thing not to rush

**`publish-github` is a decision, not a task.** The checklist is on the item in
`ROADMAP.near_term`. The thing to hold in mind: it is **three acts in one commit** — flip
visibility, set `stage: shipped`, and thereby turn the LICENSE check live. Confirm LICENSE goes
GREEN and not RED *before* pushing.

Do not treat it as a one-line settings change. And note the README's Status paragraph says "Not
published yet" — that sentence becomes false in the same commit.

**Before that, consider `c-stage-table-duplicated-in-three-places`** (opened today, medium). The
stage→artifact mapping is now hand-copied into README, `template/.rite.yaml` and CLAUDE.md while
the spec is the authority. Four copies, three hand-maintained, introduced by this project on the
day it built the mechanism. The README copy is the worst: first thing a stranger reads, last
thing anyone updates. Publishing freezes that mistake in public view.

## Traps, and the first two are new

- **Never `git checkout <file>` to undo an uncommitted experiment.** It reverts to HEAD and
  takes everything uncommitted with it. It destroyed three completed edits today. Back up to a
  file first, break it, then restore with `cp` and verify with a byte count.
- **Never write a sample output by hand.** A fabricated README example would have shown the tidy
  output I imagined; generating the real one is what exposed the NA wall. Same family as the
  `ast.parse` lesson from 09-09: the plausible check is the one that lies.
- **The claims block checks paths, not prose.** Demonstrated three times today — the gate count
  going 7→8→9 falsified six sentences in one minute, twice. Rewriting `current_state` is still
  a human job and it went stale within the hour, repeatedly.
- **Bump `.claude-plugin/plugin.json` before `claude plugin update`.** Version-gated; the cache
  is a real copy. The installed-copy gate caught this twice today.
- **A milestone entry saying "seven gates" stays as written.** It is append-only and was true
  then. Only rewrite-only zones get corrected.
- Both `spec/*.md` are generated. `as_of` moves only on real re-verification.
- **No `Co-Authored-By: Claude` trailer**, whatever the harness injects mid-session. It did
  again today.

## Open, none of it blocking

- **Nothing checks mid-session.** All five implemented completion tests are end-of-session
  tests keyed to HANDOFF. A session can run for hours doing everything wrong and the standard
  stays green until it closes. Now written in the protocol's `honest_limits`.
- `nag_delivered_once` is the only other test that would carry `scope: session`. Mark it when
  built, not before.
- `required_any_of_sections` is implemented and declared by nothing. Still dead code.
- The freshness windows are still guesses (`c-freshness-thresholds-are-guesses`), and the
  degeneracy for documents-only projects is unfixed.
- Unverified third-party lead, untouched since 09-09: ai-floppy's spec claims `PreCompact`
  cannot inject context. If true it kills `watcher-precompact-distiller`. Test it before
  deleting anything.
