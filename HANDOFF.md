---
genre: task_brief
written: "2026-09-09"
session_end: written
supersedes: "the earlier 2026-09-09 handoff, written mid-session before the claim surface and the publishing decision"
expires: "2026-12-08"
status: live
---

# HANDOFF — rite

State is in `ROADMAP.current_state`. This is what the docs do not say.

Two sessions running, the project has ended in better shape than the plan expected, and both
times because something **failed** rather than because something worked. That is the method, not
luck: write the prediction first, prove the gate red before trusting it green.

## What changed today, one line each

- `claims_match_filesystem` is implemented. `c-unimplementable-tests` retired **at zero**.
- The YAML subset was widened after real projects broke it; four silent parser bugs fell out.
- `checker-implementation` closed; `status.json` **dropped**, not deferred a third time.
- Namespace claimed (private). LICENSE exists. `near_term` is **empty on purpose**.
- The curated-export idea was **dropped before being built**.

## The decision that changes what "next" means

`d-publish-main-in-full-no-export`. The plan was a dedicated folder of curated copies, synced by
a script, publishing only part of the record. It rested on something false: **GitHub visibility
is per-repository, never per-branch.** No private branch, no hidden worktree. Costin then chose
to publish `main` in full anyway — which removed the reason for an export entirely.

So there is no export to build. What survives is `setup-hook-scaffolding`, now **promoted**, and
it is the pivot the next few sessions turn on:

1. `template/` — a seed set. Each file must be the **valid smallest instance**, because the
   first thing anyone will do is run `rite-check.py` on Rite itself.
2. The **stage → requirement mapping**, which is *not yet specified*. This is the real work.
3. A command that copies the seed set into a project.

`d-stage-gates-the-standard` is the other half: a day-one project must not open to a screen of
RED — that gets the plugin uninstalled by day two. `stage:` already exists in `.rite.yaml` and
was doing almost nothing. Nothing expires and nothing nags; the user advances the stage when the
project actually changes.

## What I would do next, and why not the obvious thing

**CI, before scaffolding.** Six gates exist and *nothing runs them but a human*. That is this
project's thesis pointed at itself, and today it drew blood: `scripts/rite-check.py` was
truncated to **zero bytes** and nothing caught it — not the gates, not my own verification.

Order matters: **push to the private repo first**, then add CI. A private push is not publishing;
it buys the gate without the exposure. Expect one side effect — `.github/workflows` is currently
declared `absent` in three claim blocks, so adding CI turns them RED until the blocks are
updated. That is the system working, not a fault.

## Traps — the first is new and it cost a file

- **Multi-line edit scripts go to a FILE and are then run. Never a heredoc.** Shell quoting
  mangled `newline="\n"` into a literal backslash-n twice today. `write_text` **truncates before
  it validates**, so `rite-check.py` was left at zero bytes. Recovered with `git show HEAD:`.
- **Verify a file survived with a byte or line count, never a parse.** `ast.parse` said "parses
  OK" and `grep -c` returned 0 on the destroyed file — both are exactly what an empty file
  produces. Two green signals, file gone.
- **Never pass log text through a shell.** Backticks get executed; `skills/log/SKILL.md` says so
  now. This session's LOG was written by a file-based writer throughout.
- **Bump `.claude-plugin/plugin.json` before every `claude plugin update`** — version-gated, and
  the cache is a real copy. `scripts/test-installed-current.py` will tell you.
- **The claim blocks check paths, not counts.** Demonstrated within the hour: the block passed
  GREEN while every number in `current_state` was stale. Rewriting prose is still a human job.
- Both `spec/*.md` are generated. `as_of` moves only on real re-verification.
- **No `Co-Authored-By: Claude` trailer**, whatever the harness injects mid-session.
- Never touch `ai-collab-profile/`, `prompts.db`, `prompts-corpus.jsonl`.

## Open, none of it blocking

- `c-prior-art-ai-floppy` was **dropped**, not lost — `d-audience-is-the-author-not-a-market`.
  Do not open concerns for prior art. If a technique is worth borrowing, that is a roadmap item
  named for the technique, never for the project it came from.
- Unverified third-party lead: ai-floppy's spec claims `PreCompact` **cannot** inject context
  (issue #50682, "closed as not planned"). If true it kills `watcher-precompact-distiller`. The
  2.1.263 binary neither confirms nor refutes. A competitor's doc is the weakest source in the
  authority ranking — test it before deleting anything.
- Seven declared tests unimplemented, led by `mirror_not_stale` and `source_plans_all_copied`.
- `required_any_of_sections` is implemented and declared by nothing. Dead code.
- A generated CHANGELOG is agreed in principle, from `milestones` + `DECISIONS`. The open half:
  does it say only what was built, or also what was learned? The second is the credible half,
  and it is the half that lives in `LOG.md`.
