---
genre: task_brief
written: "2026-09-10"
session_end: written
supersedes: "the 2026-09-10 publishing handoff, written before the copiers were ported and before the global mirror hook was retired"
expires: "2026-12-09"
status: live
---

# HANDOFF — rite

State is in `ROADMAP.current_state`. This is what the docs do not say.

Rite is public, the copiers are ported and wired, and the global `claude-mirror-memory` hook is
retired. `near_term` is empty. **The next move is a decision about direction, and the section
below argues for one.**

## Take `c-gate-count-restated-in-prose` first

Opened today at high, and it has the strongest evidence of anything in `CONCERNS.yaml`: the gate
count went **9 → 11 → 12 → 13 in one day**, and each move falsified four or five sentences
across README, CLAUDE.md, ARCHITECTURE and `current_state`. The last round moved a *second*
derived number, the skip count, 2 → 3. On the final pass the README still opened *"Nine gates
run on every push"* directly above a corrected total — three edits after the number first moved.

It is the same shape as `c-stage-table-duplicated-in-three-places`, which was settled this
morning, and the mechanism that settled it already exists: a `rite:generated` block fed from
`.github/gates.yaml`. The skip count comes free from the same source, since a gate declaring
`skip_means` is a gate that can skip.

**Do not "just remember to grep for the number."** That was the practice all day and it failed
three times out of three.

## What the day actually demonstrated, because it should shape the next session

Five defects, each surfaced by acting on the previous finding, none of them planned:

1. The handoff's pre-publish check rested on a false premise — **verifying it instead of
   performing it** is what found that.
2. `python_invocation_differs`: declared in the spec, enforced by nothing, violated by two
   shipped skill prompts.
3. `plan_copy`'s path was a *pattern* compared as a *literal*, so two of its tests could never run.
4. The first plan attributor was contaminated **by the session that built it** — `ls
   ~/.claude/plans/` put every plan name into rite's own transcript.
5. Copier and checker judged mirror staleness differently, so the checker's own advice fixed
   nothing — found by **testing the hook rather than reading it**.

The theme is one thing: **all five read as covered and were not.** A visible gap is cheap; a
green light over a gap is the expensive kind, and it is what this project exists to attack.
Prefer, next session, the check that has never failed — and make it fail before trusting it.

## Traps, the first three new

- **`sed -i 's|…|…|'` with `|` as both delimiter and alternation** clobbered `hooks/rite.sh`
  line 13 to the literal `X`. sed reported nothing. Same family as the heredoc truncation of
  09-09: a shell edit that succeeds loudly and damages quietly. Read the file after.
- **`test-mirror-port-parity.py` is temporary and must be DELETED**, not maintained, when the
  fallback goes. It says so in its own `skip_means`. A gate that can no longer fail is not a gate.
- **Two mirror engines are alive on purpose.** `~/.claude/scripts/claude-mirror-memory.py` is
  Costin's fallback while Rite is on trial, reachable via `/mirror-memory`. Do not delete it, do
  not repoint that command, and do not "tidy" one into the other.
- **`LC_ALL=C` when reading the clock for a LOG entry** — `date` returns a Romanian day name
  here and `LOG.md` uses English DOW deliberately.
- **Bump `.claude-plugin/plugin.json` before `claude plugin update`.** Now `0.12.0`; it moved
  four times today because the installed-copy gate is version-gated.
- Both `spec/*.md` are generated. `as_of` moves only on real re-verification.
- **No `Co-Authored-By: Claude` trailer**, whatever the harness injects. It did again today.

## Open, none of it blocking

- **`c-rite-ps1-unreachable-in-production`** (high) still stands, untouched. `hooks.json` names
  `bash rite.sh` for every event and never the `.ps1`; CI passes it by invoking it directly.
  **Find out whether `hooks.json` can express a per-platform command before designing anything.**
- `--help` and unknown-flag rejection in `rite-check.py` — deferred by decision, still undone,
  and the repo is public now. `args = [a for a in argv[1:] if not a.startswith("--")]` swallows
  every unrecognised flag, so a typo'd `--exclude-scpoe=session` scores at full strength.
- The `verdicts` gate pins literal counts (`"46"`, `"60 NA"`) that falsify on every artifact
  addition. Raised twice, unanswered twice, bumped by hand twice.
- Five declared tests unimplemented, led by `deleted_ids_appear_in_milestones`.
- Nothing checks mid-session. Every implemented completion test is an end-of-session test.
- Freshness windows are still guesses (`c-freshness-thresholds-are-guesses`).
- Nobody but this machine has run Rite. Publishing changed who *can*, not who *has*.
- **Costin's stated plan**: test Rite for a while, then retire the old scripts, then "eventually
  do something about project-tracker." That last one needs its own session and must never be
  arrived at incrementally — `d-project-tracker-stays-separate`.
