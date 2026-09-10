<!-- Copied from ~/.claude/plans/cheeky-dazzling-bonbon.md on 2026-09-10.
     Plans are written outside the project under harness-generated names carrying no
     project attribution; they are lost when the session ends unless copied. Canonical
     name per spec/project-standard.yaml artifact `plan_copy`. Copied by rite_copy.py,
     which attributes a plan to the project whose SESSION wrote it. -->

# Unpark `claims_match_filesystem` with a declared claim surface

## Context

`claims_match_filesystem` is the highest-value test in the standard and the last blocker in
`c-unimplementable-tests`. It exists to catch the api.pdf doc-rot class: **a claim that reads
perfectly and is flatly wrong.**

It has bitten **four times in two days**, every instance caught by a human noticing — the
mechanism this project exists to argue does not work:

| date | file | the false claim |
|---|---|---|
| 08-09 | `docs/ARCHITECTURE.md` | omitted `rite-check.py` entirely; called `session_start` *planned*, said it writes `status.json`, and said it reads an `/end` stamp file that `d-end-outcome-recorded-in-handoff` had **rejected** |
| 08-09 | `.rite.yaml`, `docs/CONCERNS.yaml` | "this project is currently documents-only" — false once `scripts/` existed |
| 09-09 | `docs/ROADMAP.yaml` | `current_state`: "Still NO hooks, commands or skills. Not a git repo." |
| 09-09 | `README.md` | "No plugin, no hooks, no slash commands, no packaging. The protocol is specified; nothing implements it." |

**The finding that reshapes the task:** the rule is declared on **`CLAUDE.md` only**
(`spec/project-standard.yaml:689`). Not one of the four failures was in CLAUDE.md — so even
fully implemented, it would have caught **none** of them. The scope was as wrong as the
implementation.

MISSION forbids AI inference at check time, so prose cannot be read. The blocker was never
difficulty; it was that nothing in a document is machine-addressable. This adds the smallest
thing that is.

## Why not parse the prose

Rejected after reading the real documents. `docs/ARCHITECTURE.md:105`:

```
Still planned, not built:

    hooks/            PostToolUse — belongs to port-mirror-memory
    scripts/          preflight.py port — port-preflight
```

Both paths **exist**; the annotation names what is missing *inside* them. A rule asserting
"paths in a not-built section must be absent" fires a false positive on day one — and a check
that cries wolf gets switched off within a week, which is this project's own stated reason for
keeping reporters separate from gates.

Prose stays prose. Claims become explicit.

## Design

A `claims:` block on the artifact's existing provenance surface — front matter for `.md`, top
level for `.yaml`. No new file, no new artifact; the inventory stays frozen at 13.

```yaml
---
schema_version: "1.0.0"
as_of: "2026-09-09"
status: current
claims:
  absent:
    - scripts/status.json
    - .github/workflows
  present:
    - scripts/rite-check.py
    - hooks/hooks.json
---
```

**Two rules, not one.** The engine derives a failure's severity from the test's `level`
(`rite-check.py:716,740` — `LEVEL_SEVERITY = {exists: RED, integrity: RED, populated: YELLOW,
fresh: YELLOW}`), overriding whatever the rule returns. So a single rule *cannot* answer YELLOW
for a missing block and RED for a false claim. Splitting it is what the machinery already
supports:

| rule | level | fires when |
|---|---|---|
| `claims_declared` | `populated` → **YELLOW** | the document declares no `claims:` block — it asserts nothing falsifiable about the tree |
| `claims_match_filesystem` | `integrity` → **RED** | a declared claim is false. **NA** when no block exists — nothing to verify |

**`claims_match_filesystem` moves from `fresh` to `integrity`.** It currently sits at `fresh`,
which caps it at YELLOW. A document that is *confidently wrong* is not merely stale, and the
founding failure of this project deserves the loud verdict. `integrity` already covers
content-is-wrong cases (`no_done_markers`, `written_not_older_than_newest_log_entry`).

**Semantics, deliberately dumb:**
- every path in `claims.absent` must NOT exist → if one exists, RED naming it
- every path in `claims.present` MUST exist → if one is missing, RED naming it
- a malformed block (not a mapping, values not lists of strings) → RED, never ignored. A claim
  surface that silently does nothing is the defect being fixed.

Existence uses `ritefs.exists_exactly` (`scripts/ritefs.py`), so a claim cannot pass on macOS
and fail on Linux — `d-one-implementation-of-a-portability-rule`.

**A new pattern, stated deliberately:** every existing rule takes its config from the *spec*
(`test.value`, `art.structure.*`). This is the first whose config comes from **the artifact
being checked**. That is the point — each project declares its own claims — but it is new, and
belongs in the spec prose rather than discovered later.

**Why it does not just move the rot:** prose is vague and unfalsifiable ("no plugin"); a path is
not. `absent: [.claude-plugin/plugin.json]` costs one line and fails the instant it becomes
true. The discipline becomes: *when you write a "not built" sentence, name the path.*

**Honest limit, to be written into the rule's `means:`:** this catches path-shaped claims only.
ARCHITECTURE's "writes `status.json`" is a claim about *behaviour* and stays uncaught. Three of
this week's four failures were path-shaped; the fourth was not.

## Files to change

**`scripts/rite-check.py`**
- add `@rule("claims_match_filesystem")` and `@rule("claims_declared")`, signature
  `(ctx, art, test)` returning `(severity, message)` — the decorator registry at `:237`
- read the block via existing `_meta(ctx, art)` (`:657`), which already returns front matter
  for `.md` and the top-level mapping for `.yaml`. No new parsing path.
- resolve paths with `ritefs.exists_exactly`; reuse, do not reimplement

**`spec/project-standard.yaml`**
- declare both rules on the artifacts that actually make filesystem claims: `readme`,
  `claude_md`, `architecture`, `roadmap` — all tier 0/1. **Not** `mission`: its `non_goals` are
  statements of intent, not of the tree.
- move `claims_match_filesystem` from `level: fresh` to `level: integrity`
- document the `claims:` block once, in the structure/provenance prose, with the honest limit
- regenerate with `python3 spec/render-standard.py`; **never edit the `.md`** — two gates

**`scripts/test-checker-verdicts.py`** — extend, do not add a file:
- `absent` path that exists → RED naming it; `present` path missing → RED naming it
- both satisfied → GREEN; no block → YELLOW from `claims_declared`, NA from the other
- malformed block → RED
- case trap: `README.MD` declared present while `README.md` is on disk → must fail on Linux
  **and** macOS

**Rite's own documents** — declare real blocks, which is also the first live test:
`README.md`, `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.yaml`.

## Verification

1. **Prove it red first.** Run the extended `test-checker-verdicts.py` against the unmodified
   checker and confirm failures — as with the last three gates.
2. `python3 scripts/rite-check.py` — rite stays 0 RED once its blocks are written and true.
3. **Plant a lie:** temporarily add `absent: [scripts/rite-check.py]` to README's block,
   confirm RED naming that path, remove it.
4. **The retrospective test, the one that matters:** check out `71edd82`, add the claim blocks
   that should have been there, and confirm RED on the four historical failures. *A rule that
   cannot catch the failures that motivated it is not worth shipping.*
5. `render-standard.py --check` and `--protocol --check` — both OK.
6. `python3 scripts/test-riteyaml.py` — the spec still parses.
7. `rite-check.py ~/projects/{hwprivacy,plumbing,claude-persistent} --force` — RED counts
   **unchanged**; they gain YELLOW from `claims_declared`, which is the intended nudge, and NA
   from the other. Confirm no RED moves.
8. Bump `.claude-plugin/plugin.json`, `claude plugin update rite`,
   `python3 scripts/test-installed-current.py`.

Coverage moves from 49/57 to roughly 57/64 — 8 new declared tests, all implemented. Exact
numbers reported from the run, not predicted.

## Recording

- `DECISIONS.yaml`: the claim-surface decision, superseding the 08-09 deferral; note that the
  rule's *scope* was as wrong as its implementation, and that config-from-the-artifact is a new
  pattern.
- `CONCERNS.yaml`: `c-unimplementable-tests` reaches zero remaining — retire as settled.
- `ROADMAP.yaml`: delete "Machine-readable doc claims" from `deferred_deliberately`.
- `LOG.md` throughout, via a shell-safe writer — never `echo`.

## Side finding, not fixed here

`required_any_of_sections` is implemented (`rite-check.py:305`) but declared by no artifact —
dead code. Logged, not addressed, since it is unrelated to this change.

## Out of scope

- Backfilling claim blocks into the other 11 projects. Migration stays opt-in; they will show
  the new YELLOW, which is the nudge and not a failure.
- Behaviour claims. Named as a limit, not solved.
- Generating prose from the claim block — the `render-standard.py` pattern, a much larger
  machine. Revisit only if prose and blocks are observed to diverge in practice.
