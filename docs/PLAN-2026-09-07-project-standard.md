<!-- Copied from ~/.claude/plans/fancy-frolicking-clock.md on 2026-09-07.
     Plans are written outside the project under harness-generated names carrying no project
     attribution; they are lost when the session ends unless copied. Canonical name per
     spec/project-standard.yaml artifact `plan_copy`. Approved and executed the same session. -->

# Rite — define the "fully featured project" standard

## Context

`~/projects/rite/` was created empty on 2026-09-07 to host a public Claude Code plugin:
**session lifecycle discipline enforced by checks that fail**. Before any code, the blocking
dependency is a spec that has never existed.

**The problem, measured this session:**

- The only declaration is ADR `d-docs-yaml-self-documenting` (2026-04-24) in
  `project-tracker/docs-yaml/DECISIONS.yaml`. Its title — *"project-tracker self-documents in
  docs-yaml/"* — scopes it to **one project**. 11 others imitated it by convention.
- It declares five YAML files and **omits the three artifacts that are actually universal**:
  `README.md`, `CLAUDE.md`, `LOG.md` are in 11/11 sampled projects, including the two that
  have none of the five.
- Undeclared conventions drifted: **6** naming schemes for EVOLUTION, **3** for HANDOFF,
  **2** for PLAN files, and **5** for the cold-restart checklist.
- Nothing has a completion test. Per the standing global rule: *"the rule 'update the docs
  with current state' is not enough on its own — it has no completion test."*

**Evidence base:** ~12.5 months (first prompt 2025-08-22), 462+ sessions, 1,808 LOG entries
across 50 projects, 230 ADRs, 249 memory files. The practice is proven; it was never written down.

**Outcome:** a versioned, machine-checkable standard Rite's checks consume, plus `rite/`
seeded as the first project that conforms to it.

## Decisions taken (user, this session)

| question | answer |
|---|---|
| Audience | **Public standard**; Costin-specific bits become config |
| EVOLUTION.yaml | **Out of scope** — belongs to `project-tracker` (corrected mid-session; supersedes the earlier "fold into DECISIONS" answer) |
| Non-code projects | **First-class** |
| CONVENTIONS.yaml | **Required** — the five stay one unit |

**On EVOLUTION (corrected by user):** it answers *"what can I tackle tonight?"* — a
portfolio/scheduling question, not a "what must an agent know before touching this project?"
question. Its schema confirms it: `lanes`, `nodes`, `edges`, `branches`, `progress`,
`slippages` is a **timeline renderer** format. It is `project-tracker`'s artifact and stays
there. Rite's spec declares it **explicitly out of scope** rather than absorbing it — a named
boundary, so the next session doesn't re-litigate it. Nothing from EVOLUTION moves into
DECISIONS.

Consequence: the `vocabulary:` enum block stays with project-tracker too. But Rite's tiering
depends on a project *stage*, so **Core defines its own minimal stage vocabulary**, and
project-tracker's `projects.yaml.stage` maps onto it in the **Local** layer. Strangers have no
project-tracker, so Rite cannot depend on it for tiering.

## What the survey changed

Five findings that reshape the spec (full survey ran this session across hwprivacy,
astrolabe, project-tracker, api.pdf, plumbing, plan-evacuare):

1. **`as_of:` is the missing keystone.** `plumbing` — the *non-code* project — is the only
   one that versions its core files, using a provenance header (`schema_version`, `as_of`,
   `status`, `applies_from`, `basis`). Nothing else in the corpus lets a checker distinguish
   "current" from "stale" without guessing at mtimes. **Making a minimal provenance header
   mandatory is what makes level-3 completion tests possible at all.** It is also the single
   cheapest addition.
2. **EVOLUTION is the only properly-specified file in the corpus** — `schema:
   project-evolution`, `schema_version`, `generated_at`, `generated_from`, and a
   `vocabulary:` enum block declared *"fixed — renderers must reject anything else."*
   It is **out of scope** (see above), but it is the corpus's proof that this kind of rigour
   is achievable in practice. Rite's spec should meet that bar, not the looser bar set by the
   files it actually governs.
3. **HANDOFF has no expiry marker anywhere** — confirmed across 5 samples. No `spent`,
   `expires`, `consumed`, or `valid_until`. And there are **three genres**, not one: state
   handoff, prompt handoff (a literal paste block), task-brief handoff. The spec should name
   the genres rather than force one shape, and add expiry to all three.
4. **Two projects independently invented a staging area for unsettled items** — api.pdf's
   `CONCERNS.yaml`, plumbing's `settled:`/`open:` split. Convergent invention is strong
   evidence. Canonize it: DECISIONS holds settled calls, a declared staging area holds
   proposals, so "don't rehash decisions" finally has somewhere to put the unsettled ones.
5. **ARCHITECTURE.yaml is the least standardized file** and plumbing's is a *physical
   topology*. The spec must keep its required-key core small enough that hwprivacy and a
   plumbing schematic both pass. Say so explicitly rather than pretending to a schema.

Also worth canonizing from api.pdf/hwprivacy ADR practice: `reconstructed: true` (entry
rebuilt from code, not contemporaneous), `revisit_when:` (the only sanctioned reopen path),
`proposed_by:` / `confirmed_by_user:` provenance (34 uses), `superseded_advice:` (records
Claude's own retracted proposal so it is not re-floated), and dated post-hoc correction
blocks appended to entries instead of editing them — append-only applied *within* an entry.

## The standard

### Tier 0 — always, from creation (evidence: 11/11)

| artifact | question it answers |
|---|---|
| `README.md` | What is this, and how does a human start? |
| `CLAUDE.md` | What must an agent know before touching this? |
| `LOG.md` | What happened, in order — append-only |

Never declared before. They are the actual floor. `CLAUDE.md` gets a declared section set,
drawn from what already recurs across 10 projects: *Read first · What this is · The one
insight · Traps that produce plausible-but-wrong output · Don'ts (in all 10) · Explicitly NOT
built · Locked findings · Relationships · Response style*.

### Tier 1 — once committed (stage ≥ spec) (evidence: 9/11, adopted all-or-nothing)

| artifact | question it answers |
|---|---|
| `docs-yaml/MISSION.yaml` | Why does this exist? Constraints, non-goals |
| `docs-yaml/ARCHITECTURE.yaml` | What lives where; flow; ownership. **Loosest schema — by design** |
| `docs-yaml/CONVENTIONS.yaml` | Format and vocabulary rules for this project |
| `docs-yaml/DECISIONS.yaml` | Settled calls — do not rehash |
| `docs-yaml/ROADMAP.yaml` | Near / mid / long + the cold-restart checklist |

The cold-restart checklist is canonized under **one** key name (currently five), because it
is present in every project sampled — universal in practice, nameless in the spec.

### Tier 2 — situational, canonical names (kills the drift)

| artifact | rule |
|---|---|
| `HANDOFF.md` | One name, three declared genres, **mandatory expiry marker** |
| `docs-yaml/PLAN-YYYY-MM-DD-<slug>.md` | Canonical name for a plan copied out of `~/.claude/plans/` |

Expiry is not decoration: `claude-persistent/HANDOFF.md` is marked *"spent"* in a sibling
file and still sits in the project root reading as authoritative.

### Tier 3 — generated, never hand-edited

`docs-yaml/claude-memory.md` — written by the `claude-mirror-memory.py` PostToolUse hook.

### Required provenance header (every `docs-yaml/*.yaml`)

```yaml
schema_version: "1.0.0"
as_of: "YYYY-MM-DD"     # what this file was last verified against
status: draft | current | superseded
```

Modeled on `plumbing/docs-yaml/`. Three lines, and they are what make staleness checkable
instead of inferred.

### Core vs Local

Two marked layers in one document, so the spec is publishable:

- **Core** — artifact set, purposes, required structure, completion tests.
- **Local** — LOG line format (EU date order, English DOW, `short_name`), the `[TYPE]` tag
  vocabulary, registry integration (`projects.yaml`), `docs-yaml/` vs `docs/` naming.

## What makes this a standard and not a template

Every artifact declares a **completion test** — the check Rite runs on the *next* session if
you skipped it. Three levels:

1. **exists** — file present
2. **populated** — not still the scaffold; no unfilled placeholders
3. **fresh** — `as_of` not stale relative to code activity. Per the standing api.pdf rule:
   after the first line of code, every doc claim is a *testable assertion*, so freshness is
   measured against code/commit activity, **never against another document**

Level 3 is the differentiated part, and level 3 is only reachable because of the `as_of`
header above.

## Deliverables — written into `~/projects/rite/`

1. **`spec/project-standard.yaml`** — machine form, the authority. Artifact registry: id,
   path, tier, required-at-stage, purpose, required keys, completion tests, core-vs-local.
   Carries its own provenance header.
2. **`spec/PROJECT-STANDARD.md`** — human form, rendered on GitHub. **Generated from the
   YAML**, never hand-maintained in parallel — otherwise the spec is its own first doc-rot
   casualty.
3. **`spec/check-spec-sync.py`** — the check that fails when 1 and 2 disagree. Applies the
   project's own principle to the project's own spec on day one.
4. **`rite/` seeded with its own Tier 0 + Tier 1 set** — dogfooding. Rite must be the first
   project that passes its own standard.

## Explicitly NOT in this plan

- No plugin, hooks, skills, or slash commands.
- No port of `preflight.py` / `claude-mirror-memory.py` / `hookdedup.py`.
- No session start/end protocol spec — the companion piece, next session.
- No git init, LICENSE, GitHub repo, or namespace claiming.
- No changes to `claude-persistent`, `claude-preflight`, or `project-tracker`.
- No migration of the 11 existing projects to the new names. The spec defines the target;
  migrating is a separate, later, opt-in job.

## Verification

- `python3 spec/check-spec-sync.py` exits 0.
- `yaml.safe_load()` parses `spec/project-standard.yaml`.
- Run the standard by hand against three differently-shaped projects and **report the
  output, not a claim**: `hwprivacy` (mature code), `plumbing` (non-code), and
  `claude-persistent` (known-incomplete — it **must FAIL**, naming its missing Tier 1
  files). A standard that passes everything is not a standard.
- `rite/` itself passes Tier 0 + Tier 1.
- `yamllint` and `ruff` clean on everything written.
