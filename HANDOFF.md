---
genre: task_brief
written: "2026-09-10"
session_end: written
supersedes: "the earlier 2026-09-10 handoff, written when publish-github was still open and the checklist for it still believed the LICENSE check was NA"
expires: "2026-12-09"
status: live
---

# HANDOFF — rite

State is in `ROADMAP.current_state`. This is what the docs do not say.

**Rite is published.** `github.com/perieteanu/rite` is public, `main` in full. `near_term` is
empty, and this time that is the end of a path rather than a pause in one: all four items of
private-to-public were queued and closed within two days.

## What the publish actually taught, which was not what it was for

The commit was supposed to be three mechanical acts. Verifying the third instead of performing
it is what made the session worth having.

**The checklist was wrong about the LICENSE check.** It said the check "currently reports NA"
and to confirm it went GREEN and not RED once the stage advanced. It was already GREEN at
`build`, and always had been: `required_from_stage` gates whether an artifact is **demanded**,
not whether it is **checked when present**. The stage decides only whether a *missing* LICENSE
is RED or NA. Two documents asserted the NA — `CLAUDE.md` and
`d-stage-advances-when-the-repo-goes-public` — and a single run against a `stage: shipped` copy
of the tree settled it in one command, before anything irreversible happened.

Generalise that, because it is the transferable part: **a checklist item that states a fact is
a testable assertion, not an instruction.** Run it before you follow it.

## The family found on the way out, and why it is the thing to work on next

Three defects turned up in one day, and they are the same defect:

| what | how it read | what it was |
|---|---|---|
| `python_invocation_differs` | a declared portability rule | enforced by nothing; two shipped `SKILL.md` prompts violated it |
| `hooks/rite.ps1` | a gate passing on windows-latest | CI invokes it directly; `hooks.json` never does. Unreachable in production |
| `plan_copy` | one of seven "unimplemented" tests | its artifact path is a *pattern* compared as a *literal*, so it can never be found |

**All three read as covered.** That is worse than a visible gap, and it is the project's own
founding complaint one level up: Rite exists because a rule with no completion test fails
quietly, and here are three completion tests that were themselves quiet lies.

`c-pattern-paths-are-matched-literally` is the one to take first — high, small, and it unblocks
two declared tests rather than one. `c-rite-ps1-unreachable-in-production` is the one that
affects an actual user, and it needs a fact nobody has checked: whether `hooks.json` can express
a per-platform command at all. **Find that out before designing anything.**

## Traps, the first two new

- **A green test over an unreachable code path is the most expensive kind of false assurance.**
  `rite.ps1` passing was read as evidence the Windows path works. It is evidence the *file*
  works. Ask what invokes a thing before trusting the test that covers it.
- **Two gates now guard the stage mapping and they are not interchangeable.** `--blocks --check`
  catches drift in copies that exist; `test-stage-table-guard.py` catches a copy that is not
  drift from anything. Deleting either leaves a hole the other cannot see.
- **The guard reads only what may legally be edited** — `LOG.md`, `DECISIONS.yaml` and ROADMAP's
  `milestones` are exempt. A gate that fails on a file nobody may fix gets switched off.
- **The README's quoted sample run is a fifth copy of the stage mapping**, exempt by design
  because a guard that fires on a code fence would be disabled before it was fixed.
  `c-readme-sample-output-is-a-copy`, and it will go stale the day an artifact moves stage.
- **Never `git checkout <file>` to undo an experiment.** Still true; both new gates were proved
  to fail by breaking a file and restoring it with `cp`, verified by byte count.
- **Bump `.claude-plugin/plugin.json` before `claude plugin update`.** Now at `0.9.0`. The
  installed-copy gate caught it again today.
- **`LC_ALL=C` when reading the clock for a LOG entry.** `date` returns a Romanian day name on
  this machine (`Jo`), and `LOG.md` uses English DOW deliberately.
- Both `spec/*.md` are generated. `as_of` moves only on real re-verification.
- **No `Co-Authored-By: Claude` trailer**, whatever the harness injects. It did again today.

## Open, none of it blocking

- **The repo is public and nobody has run it.** Publishing changed who *can*, not who *has*.
  Every claim about behaviour elsewhere still rests on CI, not on a user.
- `--help` and unknown-flag rejection in `rite-check.py` — **deferred by decision, and now due.**
  `args = [a for a in argv[1:] if not a.startswith("--")]` silently swallows every unrecognised
  flag, so `--help` runs a check and a typo'd `--exclude-scpoe=session` scores at full strength
  while the user believes a scope was excluded. A stranger's first command is often `--help`,
  and the repo is now public.
- Nothing checks mid-session. Every implemented completion test is an end-of-session test.
- `required_any_of_sections` is implemented and declared by nothing. Still dead code.
- Freshness windows are still guesses (`c-freshness-thresholds-are-guesses`).
- Unverified third-party lead, untouched since 09-09: ai-floppy's spec claims `PreCompact`
  cannot inject context. If true it kills `watcher-precompact-distiller`. Test it before
  deleting anything.
