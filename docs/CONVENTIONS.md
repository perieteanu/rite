---
schema_version: "1.0.0"
as_of: "2026-09-07"
status: current
---

# CONVENTIONS — rite

*Format and vocabulary rules for THIS project. Read before editing anything that writes
`LOG.md`, the spec, or generated files.*

## Naming

- **Spec files** — kebab-case for machine forms (`project-standard.yaml`), SCREAMING-KEBAB for
  generated human forms (`PROJECT-STANDARD.md`).
- **Scripts** — kebab-case with a `.py` extension; a single script carries its modes as flags
  (`--check`), following `preflight.py` and `claude-mirror-memory.py`.
- **Docs directory** — `docs/`, never a format-bearing name. A directory called `docs-yaml`
  becomes a false claim the moment one file inside it is Markdown.
- **Canonical over descriptive** — where the corpus drifted, the standard picks ONE name and
  records what it replaces. A descriptive-but-varied name is worse than a plain canonical one,
  because it cannot be checked.

## File format

Prose goes in Markdown, structure goes in YAML, and the provenance header is identical in both.

- `.md` with YAML frontmatter — MISSION, ARCHITECTURE, CONVENTIONS, HANDOFF, PLAN copies.
- `.yaml` — DECISIONS, ROADMAP. Repeated entries whose fields the completion tests read.
- The choice is per file, not per project. Test: **if a checker must read a field of it, it is
  YAML; if a human reads it end to end, it is Markdown.**
- Measured basis, this project's own spec in both forms: 25287 bytes YAML vs 19275 Markdown for
  byte-identical content — 24%. YAML charges a `key:` and an indent on every line of prose.

## Language

- Docs in English.
- Never translate Romanian domain terms into English.
- Tone: dense, terminal-native. No emojis. No marketing language.

## Generated files

- A generated file carries a DO-NOT-EDIT banner naming its source and its regeneration command.
- **No timestamps.** Generated output must never contain a generation time, hostname, or any
  value that changes between identical runs. A non-deterministic generator makes its own drift
  gate fail constantly, and a gate that always fails gets switched off.
- Current generated files: `spec/PROJECT-STANDARD.md`.

## Logging

- File: `LOG.md`
- Format: `DD-MM-YYYY HH:MM[:SS] | DDD | rite | [TYPE] description` — **seconds are optional**.
- short_name: `rite`
- Date order: European — deliberate.
- Day of week: English 3-letter, fixed width. System locale is `ro_RO`, so ALWAYS force `LC_ALL=C`.
- Time source: the machine clock. Never invent, round, or approximate.
- **No spacing rule.** Entries carry the time they were actually written, even when several
  share a second. The old *"≥1 minute apart"* rule was deleted on 2026-09-08 because it
  **mandated fabrication**: when six things happen inside one minute it forces you to invent
  spacing — and that is exactly what produced ~30 invented timestamps on 2026-09-07. A rule
  written to keep the log honest was the rule forcing the lie.
- Ties are broken by file order, which is insertion order. Sort by timestamp, then by position.
- Seconds are **additive, not a migration**: minute-precision entries stay valid forever and are
  re-emitted byte-identically. Nothing is rewritten, so append-only is never violated.
  Round-trip proof: `project-tracker/test-log-roundtrip.py`.

## Write discipline

Every file declares exactly one. "Edit the docs" means five different things, and getting it
wrong fails silently — an appended roadmap becomes a graveyard, a rewritten log destroys the
only durable record, an edited plan falsifies what was actually approved.

| file | discipline |
|---|---|
| `LOG.md` | append-only |
| `docs/DECISIONS.yaml` | append-only (and within an entry too — corrections are dated blocks) |
| `README.md` `CLAUDE.md` | rewrite-only |
| `docs/MISSION.md` `docs/CONVENTIONS.md` | rewrite-only |
| `docs/ARCHITECTURE.md` | rewrite-only, and **must always be current** — see below |
| `docs/ROADMAP.yaml` | **mixed, 3 zones** — `inception` write-once, body rewrite-only, `milestones` append-only |
| `docs/CONCERNS.yaml` | **mixed** — entries mutate, `retired_ids` append-only |
| `HANDOFF.md` | write-once |
| `docs/PLAN-*.md` | write-once |
| `spec/PROJECT-STANDARD.md` | free-replace (generated) |
| `docs/claude-memory.md` | free-replace (generated, single file) |
| `LICENSE` | write-once — and the **only** file that must NOT carry a provenance header |

The inventory is **frozen at 13** as of 2026-09-07. Frozen means: this is the complete list of
files a human or an agent *authors*. Script-produced files are specified separately, once their
producers exist — a generated artifact can only be specified honestly when something real
generates it. Adding a 14th is a DECISIONS entry, not a good idea in the moment.

- **append-only** — never rewrite existing content; only add, at the end. Append a dated
  correction block rather than editing. Exception: one-time format migrations, logged as such.
- **rewrite-only** — states current truth; stale content is DELETED, never annotated. The
  hazard is accumulation: a rewrite-only file that only ever grows has silently become
  append-only and stopped being true.
- **write-once** — frozen at a *declared moment*, not at the first keystroke. `HANDOFF.md`
  freezes at session end; `PLAN-*.md` at copy; ROADMAP `inception` at project birth. Before
  that moment it is drafted freely; after it, a change means a new file or a DECISIONS entry.
- **free-replace** — overwritten wholesale from a declared source; local edits are discarded
  by design.
- **mixed** — must name, inside the file, where the line falls. A mixed file that does not say
  is worse than either pure form.

**File order is insertion order and MAY differ from chronological order.** Any consumer must
sort by parsed timestamp before displaying, ranking, or aggregating.

## ARCHITECTURE must always be current

It describes the shape of the thing as it is *now*. MISSION is near-static and DECISIONS is a
growing record, but ARCHITECTURE has no legitimate stale state — a wrong architecture doc
actively misroutes the next session. Rewrite it in the same session the shape changes, not at
the next audit.

## Who owns "current state"

`docs/ROADMAP.yaml` `current_state` owns it. `README.md` carries a one-line mirror — there is a
**no longer a tested link** — `claims_match_stage` was removed on 2026-09-08 (see
`d-drop-claims-match-stage`) and nothing replaced it. The failure it was written for — a README
asserting *"no extension code yet"* over a running extension — is a claim about the FILESYSTEM,
and belongs to `claims_match_filesystem`, which is still unimplemented. `HANDOFF.md` **references** it and
must not restate it. Four files claiming current state was the measured condition here on
2026-09-07.

`deferred_deliberately` (ROADMAP) means **"yes, later"**. `non_goals` (MISSION) means
**"never"**. Not the same list; an item in the wrong one silently changes the answer to
*"should we do this?"*.

## The inception block

`ROADMAP.inception` is written **once**, at project birth, and never edited — not even to fix a
name that later changed. `current_state` is rewrite-only, so the original intent is destroyed
the first time the roadmap is adjusted; without a frozen baseline there is nothing to compare a
milestone against. Drift-from-original is the one thing `LOG.md` cannot reconstruct: the log
says what happened, never what was intended before it changed.

A genuine re-agreement is a DECISIONS entry, never an edit to `inception`.

## Closing a roadmap item

Delete it from `near_term` and append one entry to `milestones` naming its `id`. Never mark it
done in place.

`LOG.md` and `milestones` are two *resolutions* of the same past, not two copies of it. The log
records every choice and every implementation step; milestones record only what a near_term
item delivered. The log answers *"what happened on the 7th"*; milestones answer *"what has this
project actually shipped"*. Neither is cheaply derivable from the other — the log is too fine
to skim, milestones too coarse to debug from.

`milestones` is a flat list and stays one. Lanes, nodes, edges, progress and slippages are
`EVOLUTION.yaml`, which renders a timeline, answers a scheduling question, and belongs to
project-tracker. This is the nearest point at which Rite can drift into that product by
accident.

## Explicit nothing beats absent

Where a file or section has no content, it must SAY so in one line rather than sit empty or
missing. `CONVENTIONS` with no project-specific rules says exactly that and passes; an empty
one does not. A `HANDOFF` with genre `none` states there is nothing to hand off and passes; a
missing one proves nothing. The two look identical from the next session's side except that one
of them proves somebody decided.

## No hardcoded values

- Anything tunable lives in a human-visible config file (YAML), never inline in code.
- Applies to: thresholds, paths, check toggles, staleness windows.
- Anti-example: claude-persistent shipped a hardcoded model→context-window map that went stale
  on a model release and silently reported 55% of 200K on a 1M session. The map won over
  inference because it claimed to be exact. Hardcoded tables lose to derivation.

## Testing

- **Every check must be shown FAILING before it is trusted.** A check that has only ever been
  observed passing has not been observed at all. The spec drift gate was verified by
  hand-editing the generated file and confirming exit 1.
- Plain Python. No AI inference at check time; every result must be re-derivable.

## Portability

Cross-platform is a MISSION constraint, so these are rules, not preferences. All of them were
derived by asking what breaks on Windows and macOS — none has yet met a real non-Linux machine,
so treat them as predictions to re-check on first contact.

- **Never `Path.exists()` for an artifact.** List the directory and compare names exactly.
  macOS and Windows are case-insensitive, so `README.md`.exists() is True for `readme.md` — a
  repo with `readme.md` passes there and fails on Linux. Same repo, two verdicts.
- **Generated files are written `newline="\n"`.** The platform default turns them CRLF on
  Windows and every line reads as changed across machines.
- **Normalize line endings before any byte comparison.** VS Code on Windows saves CRLF; PyYAML
  parses it fine, but `append_only_preserved` would fail on a file nobody touched. Chosen over
  a `.gitattributes` because that would be a hand-authored 14th file, and the inventory is
  frozen.
- **Shell is permitted in exactly one place: a launcher shim.** It tries `python3`, then
  `python`, then `py`; on success it execs the real work, on failure it prints what is missing
  and how to install it, and exits non-zero. Nothing else — no checks, no parsing, no logic, no
  coreutils, no `LC_ALL`, no `date(1)`.

  **Two shims — `.sh` and `.ps1`. Never `.bat`.** Verified against the hooks docs: a hook's
  `shell` field defaults to `bash`, or to `powershell` on Windows when Git Bash isn't
  installed. `cmd.exe` is never the hook shell on any configuration, so a `.bat` is dead code.
  `.sh` covers Linux, macOS and Windows-with-Git-Bash (the recommended Windows setup); `.ps1`
  covers Windows without it. They cannot meaningfully drift — one job each, no logic, and
  PowerShell is a real language so the `.ps1` is a translation, not a reimplementation.

  It exists to close the one hole Python cannot: the outermost prerequisite can't report its
  own absence, so the shim is the only code that runs *before* Python exists and can therefore
  say Python is missing.

  The LOG timestamp convention (`LC_ALL=C date …`) stays local-layer only; a shipped `/log`
  builds it in Python, with a fixed seven-element day tuple — the one place a hardcoded table
  is *correct* here.
- **Every read and write names `encoding="utf-8"`.** Windows defaults to cp1252 and the
  generated standard carries 171 non-ASCII characters. Omitting it passes where it is
  developed and corrupts everywhere else — the worst failure ordering there is.
- **Never write `python3` in docs or hook commands.** On Windows it is `py` or `python`.
- **Missing PyYAML degrades loudly**: run the Markdown checks, report the YAML ones as SKIPPED
  with the reason and the fix, exit non-zero. Never a traceback. PyYAML is absent by default on
  macOS *and* Windows, so this is the default first run on two of three targets — not an edge
  case. This is deliberately unlike the `enrichment` layer, which skips *silently*: enrichment
  is optional, PyYAML is core.

## Prerequisites

**Python 3 is the one declared prerequisite, and it is the only one.** No `pip install`, ever,
for the base layer — YAML is read by a stdlib-only subset parser shipped with Rite. Install
cost: Linux 0, macOS 0–1, Windows 1.

It is **declared visibly** rather than assumed: named in the README's first section, and
checked at preflight so a missing interpreter is reported as a finding rather than surfacing as
a hook that silently did nothing.

The parser **refuses rather than guesses** — an anchor, alias, tag, block literal or merge key
is an error naming the file and line. Its completion test is differential: parse every file
with both the subset parser and PyYAML and compare the structures. PyYAML is the *oracle* for
that test, never a runtime dependency.

## Verification

- Verify a doc claim against the filesystem or the host, **never against another document**.
- Errors propagate doc-to-doc and read perfectly while being flatly false. On 2026-08-02
  api.pdf had eight files asserting it had no code, a day after deployment; the only file that
  stayed correct was written from the machine rather than from a sibling doc.

## `as_of` discipline

`as_of` is the date the file's claims were last **verified against the thing they describe** —
not the date it was last edited. Reformatting a file, converting it from YAML to Markdown, or
fixing a typo does **not** move it. Only re-checking the claims does. Collapse this distinction
and every freshness test in the standard becomes mtime theatre.

## Credit

- ONE factual line in README Credits. Nothing else.
- Forbidden: `Co-Authored-By: Claude` commit trailers, badges, "AI-powered" banners.
- Author of record: Perieteanu Costin — owner, responsible party, legal author.

## LOG tag vocabulary

| tag | means |
|---|---|
| `work` | ordinary execution, no state change |
| `note` | observation or finding |
| `fix` | bug fixed |
| `decide` | decision made → also DECISIONS.yaml |
| `pivot` | direction change → also DECISIONS.yaml |
| `add` | scope addition |
| `defer` | postponed |
| `drop` | abandoned |
| `done` | completed |
