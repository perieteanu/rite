# CLAUDE.md — rite

## What this is

**Rite** defines session discipline for Claude Code and enforces it with checks that fail.
Two halves:

1. **The project standard** — what files a project must carry so a cold agent or a cold human
   can pick it up without re-deriving it. Written: [`spec/`](spec/).
2. **The session protocol** — what happens at the start and end of a session, which half is
   mechanical and which needs judgement, and what check fails if you skip it. Written:
   [`spec/session-protocol.yaml`](spec/session-protocol.yaml).

Delivered as a **Claude Code plugin** (hooks + commands + skills). Not a VS Code extension —
a plugin cannot draw UI, and that is fine, because the differentiated half is the checking.

## Read first (in this order)

1. [`docs/MISSION.md`](docs/MISSION.md) — why this exists; non-goals
2. [`docs/DECISIONS.yaml`](docs/DECISIONS.yaml) — settled. **Do not re-litigate.**
3. [`spec/PROJECT-STANDARD.md`](spec/PROJECT-STANDARD.md) — the standard itself, readable
3b. [`spec/SESSION-PROTOCOL.md`](spec/SESSION-PROTOCOL.md) — the protocol, readable
4. [`docs/ROADMAP.yaml`](docs/ROADMAP.yaml) — next, and the cold-restart checklist
5. [`LOG.md`](LOG.md) — what happened, in order

## The one insight the whole project rests on

**A rule with no completion test is not a rule.** "Update the docs with current state" has
been the standing instruction for a year and it fails quietly, because nothing ever checks it.
Everything here exists to convert that class of discipline into a check that fails on the next
session.

The corollary, and the reason this is not another template repo: templates are free and
everyone has one. Almost nobody ships **the check that fails when you don't follow it**.

## Traps that produce plausible-but-wrong output

- **BOTH `spec/*.md` files are generated.** Editing them does nothing — the next
  `render-standard.py` run overwrites them, and `--check` fails in the meantime. Edit the
  `.yaml`, then regenerate. Two gates now: `--check` for the standard,
  `--protocol --check` for the protocol. One renderer, so nothing drifts.
- **Most of a plugin is NOT code.** Skills, commands and agents are Markdown prompts Claude
  interprets; hooks are JSON config; scripts are the only executable component. So `/end`,
  `/log` and `/handoff` need no interpreter at all, and only preflight, the checker, the
  mirror and plan-copy need Python. See `d-plugin-components-are-mostly-prompts`.
- **Never put a timestamp in generated output.** A clock in `PROJECT-STANDARD.md` would make
  `--check` fail on every run, and a gate that always fails gets switched off within a week.
- **`as_of` is not an edit date.** It is the date the file's claims were last *verified
  against the thing they describe*. Fixing a typo does not move it. This distinction is the
  whole basis of the freshness tests; collapse it and the tests become mtime theatre.
- **Do not verify a doc claim against another doc.** After the first line of code exists,
  every doc claim is a testable assertion. Check it against the filesystem or the host.
- **`docs/` is deliberately mixed, and the split is per file, not per project.** MISSION,
  ARCHITECTURE and CONVENTIONS are Markdown with YAML front matter because they are prose;
  DECISIONS and ROADMAP are YAML because the completion tests read their fields. Do not
  "tidy" one into the other. The rule: *if a checker must read a field of it, it is YAML; if
  a human reads it end to end, it is Markdown.* See `d-docs-dir-and-format-split`.
- **Never rename the docs directory after a format.** It was `docs-yaml/` and became a false
  claim the moment a `.md` landed in it. `docs/` is format-neutral on purpose.
- **Every file declares a write discipline, and they are not interchangeable.** `LOG.md` and
  `DECISIONS.yaml` are append-only. `ROADMAP.yaml` and `CONCERNS.yaml` are *mixed* and say so
  inside themselves. `HANDOFF.md` and `PLAN-*.md` are write-once — a change means a NEW file,
  never an edit. Everything else in `docs/` is rewrite-only: stale content is **deleted**, not
  annotated. Full table in `docs/CONVENTIONS.md`.
- **`ROADMAP.inception` is write-once.** Set at project birth, never edited — it is the only
  baseline that makes drift measurable. A re-agreed plan is a DECISIONS entry, not an edit.
  `PLAN-*.md` is something else entirely: an archive copy of a `~/.claude/plans` file, made by
  tooling, many per project.
- **`current_state` is owned by ROADMAP.** README mirrors one line of it; HANDOFF references it
  and must not restate it.
- **Closing a roadmap item means DELETING it and appending a `milestones` entry** naming its
  id. Never mark it done in place. `milestones` is a flat list — the moment it grows lanes,
  nodes or progress it has become `EVOLUTION.yaml`, which belongs to project-tracker.
- **Cross-platform rules are load-bearing, not hygiene.** Never `Path.exists()` for an
  artifact (macOS/Windows are case-insensitive, so `readme.md` passes there and fails on
  Linux — same repo, two verdicts). Generated files write `newline="\n"`. Normalize line
  endings before any byte comparison. Every read/write names `encoding="utf-8"`. Never write
  `python3` in docs — Windows has `py`. **Every entry point calls `ritefs.use_utf8_stdio()`
  before printing, and every read of another process names `encoding="utf-8"` AND
  `errors="replace"`** — Python picks the console codepage for stdout on Windows, so `·` and
  `—` go out as cp1252 there and a UTF-8 parent dies on byte 0x97. CI proved this on 2026-09-10.
  Full list: `portability:` in the spec.
- **Stdlib only. There is no PyYAML dependency and nothing to `pip install`.** YAML is read by
  a subset parser shipped with Rite — measured: the project uses no anchors, aliases, tags,
  flow mappings, block literals or merge keys. The parser **refuses rather than guesses**, and
  its test is differential against PyYAML as an oracle. Do not "simplify" it into guessing, and
  do not reintroduce the dependency. See `d-stdlib-only-yaml-subset`.
- **The artifact inventory is FROZEN at 14** (13 on 2026-09-07; `script_copy` added 2026-09-10
  by `d-session-scripts-are-the-fourteenth-artifact`, which is the process working rather than
  the freeze failing). A 15th requires a DECISIONS entry.
  Script-produced files are out of the freeze until their producers exist. `status.json` and
  `checks.yaml` are deferred pending purpose; an `/end` stamp file was **rejected** — the
  outcome goes in HANDOFF front matter.
- **`LICENSE` is the one file that must NOT carry a provenance header.** It is third-party text
  reproduced verbatim; editing it changes its legal meaning. **`required_from_stage` gates
  whether an artifact is DEMANDED, not whether it is CHECKED when present** — LICENSE exists,
  so `min_lines` and `no_provenance_header` run and pass today at stage `build`. This bullet
  used to say the check "is NA until the commit that publishes", which was false and was caught
  on 2026-09-10 by running the checker against a `stage: shipped` copy. The stage decides only
  whether a MISSING LICENSE is RED or NA.
- **STAGE gates the standard, not tier.** Every artifact declares `required_from_stage`, and a
  project is not asked for what its stage has not reached. **The mapping is NOT repeated here** —
  it lives in `spec/project-standard.yaml` and is generated into README and `template/.rite.yaml`
  as a `rite:generated` block. This bullet used to enumerate it, which made a fourth
  hand-maintained copy; `spec/render-standard.py --blocks --check` and the stage-table guard
  are what replaced it. **A declaration beats tier**; `tier` is now only a grouping label and
  the fallback when no stage is declared. **Deleting `stage:` does not make the standard
  lenient** — it reverts to the stricter tier behaviour, because absence is not a claim.
  See `d-stage-is-the-gating-axis`.
- **`HANDOFF.md` always exists — required from stage `idea`, the earliest there is.** Nothing to
  hand off is written as `genre: none`, not as a missing file. Every session ends having
  recorded one of four outcomes: written, updated, carried_forward, none.

## Don'ts

- **Do not fork `claude-preflight`.** Rite is its *upstream*. Costin's preflight becomes a
  `checks.yaml` config of the Rite engine, so there is exactly one codebase and nothing to
  drift. A fork would recreate, in code, the doc-rot problem this project exists to solve.
- **Do not claim `EVOLUTION.yaml`, `projects.yaml`, or `next-steps.yaml`.** They belong to
  `project-tracker`, which answers *"what should I touch tonight?"* while Rite answers *"did
  this session close properly?"*. Integration is possible but requires its own dedicated
  session — never arrive at it incrementally. See `d-evolution-out-of-scope`,
  `d-project-tracker-stays-separate`.
- **NEVER touch `ai-collab-profile/`, `prompts.db`, or `prompts-corpus.jsonl`.** Costin's
  longitudinal self-profile — personal data, his alone, permanently out of scope. Not a
  feature, not enrichment, not an optional layer, not a documentation example. This is a
  privacy boundary and it does not soften because Rite is published. See
  `d-profiling-never-integrated`.
- **`ai-collab-interaction/` is UNRESOLVED — ask before using it.** It holds
  `session-frame.yaml` (collaboration technique, not personal data), which is the drafted
  start-session protocol Rite's second half would otherwise build on. It sits in the same
  family as the profile corpus, so treat it as off-limits until Costin rules on it.
- **Do not add hardcoded values.** Anything tunable goes in a human-visible config file.
- **No `Co-Authored-By: Claude` commit trailer.** One line in README Credits, nothing else.
- **Do not migrate the 11 existing projects** to the canonical names as a side effect of
  other work. The standard defines the target; migration is separate and opt-in.

## Locked findings (do not re-research)

- A Claude Code plugin can contain `hooks/`, `commands/`, `skills/`, `agents/`, `scripts/` —
  verified against `anthropics/claude-plugins-official`. One plugin holds the whole product.
- `SessionEnd` exists as a hook event (verified in the 2.1.263 binary alongside `Stop`,
  `PreCompact`, `SubagentStop`). **But it fires when there are no turns left**, so it can only
  do mechanical work. Judgement work must happen before, via a command.
- **A plugin and a marketplace are different things** — an earlier version of this finding
  conflated them. A single PLUGIN is `.claude-plugin/plugin.json` at its own root, plus
  `skills/`, `hooks/`, `scripts/`. A MARKETPLACE is `.claude-plugin/marketplace.json` listing
  plugins by source path. Rite is both: the repo root is the plugin, and it advertises itself
  with `"source": "."`. Corrected and verified against the plugins reference, 2026-09-08.
  `--sparse` limits checkout for monorepos; it does not relocate a manifest.
- **`commands/*.md` is the legacy form.** New plugins use `skills/<name>/SKILL.md`; both load
  identically. A plugin skill is invoked as `/rite:<name>`, and
  `disable-model-invocation: true` makes it user-only.
- Publishing a plugin = pushing a git repo. No registry, account, review, or fee.
- Licensing/trademark homework is done and the verdict is GO — see
  `~/projects/claude-persistent/docs-yaml/RESEARCH-licensing-delivery.yaml`. MIT, a distinct
  non-"Claude" name, nominative "for Claude Code", unofficial disclaimer.

## Explicitly NOT built yet

**This section was rewritten on 2026-09-09, and what it used to say is the reason the
`claims:` block below exists.** It read: *"No plugin, no `hooks/`, no `commands/`, no
`skills/`, … no git repo, no LICENSE, no packaging, no namespace claimed … nothing that
implements it does."* Every clause was false, some for two days, in the file whose whole job
is to stop an agent producing plausible-but-wrong output. Correction paragraphs had been
appended beneath it rather than the false paragraph being deleted, so the document contradicted
itself and the first thing a reader met was the lie.

What is genuinely not built, as of 2026-09-10:

- **CI runs THIRTEEN gates, but only ten of them on a runner.** `.github/workflows/gates.yml`
  fires on every push. `test-riteyaml.py` skips there (PyYAML is its oracle and CI does not
  install it) and `test-installed-current.py` always skips (a runner has no installed plugin).
  The runner reports that coverage instead of showing an unqualified green — a skip is never
  folded into a pass. It runs on **ubuntu, macos and windows** with `fail-fast: false`.
- **None of the eight watchers.** The `PostToolUse` hook itself now exists — added 2026-09-10
  with the copier port — but it does one job, refreshing the memory mirror when a memory file
  is written. `watcher-write-discipline` and the other seven are unbuilt.
- **No port of `preflight.py` or `hookdedup.py`**, and no `checks.yaml` — `port-preflight` has
  not started. `claude-mirror-memory.py` IS ported, as `scripts/rite_copy.py`, alongside plan
  and session-script copying; the global hook in `~/.claude/settings.json` is deliberately
  still running beside it until the port is proven.
- **Published 2026-09-10.** `github.com/perieteanu/rite` is PUBLIC, `main` in full including
  `LOG.md`, per `d-publish-main-in-full-no-export`. This bullet said "Nothing published" until
  that commit. What is still true: **nobody but this machine has run Rite**, so every claim
  about how it behaves elsewhere rests on CI, not on a user.
- **Seven declared tests unimplemented**, of which `mirror_not_stale` and
  `source_plans_all_copied` are the ones that matter.

**`status.json` is DROPPED, not pending** — `d-status-json-dropped-not-deferred`. Every
candidate consumer is unbuilt and the verdict it was to carry already reaches the model live.
Its shape is preserved in that decision as a sketch, not a commitment.

<!-- rite:claims
# The machine-checkable half of the section above. Prose may say whatever it needs to; these
# lines fail the day they stop being true. Add a path here whenever you write a sentence
# claiming something does not exist — that is the whole discipline.
absent:
  - commands
  - checks.yaml
  - scripts/preflight.py
  - scripts/claude-mirror-memory.py
  - scripts/status.json
present:
  - .github/workflows
  - .github/gates.yaml
  - scripts/rite-check.py
  - scripts/riteyaml.py
  - scripts/ritefs.py
  - hooks/hooks.json
  - hooks/rite.ps1
  - skills/end/SKILL.md
  - .claude-plugin/plugin.json
  - .claude-plugin/marketplace.json
  - LICENSE
-->


Note the distinction, because the two lists are easy to confuse: this section is **not built
yet** — planned, will exist. `ROADMAP.deferred_deliberately` is **yes, later**; MISSION
`non_goals` is **never**. Three different answers to "should we do this?".

## Relationships

- **`claude-preflight`** — becomes a *config* of Rite, not a fork. Its session-START half is
  the working prior art: months of real use, two enforcement checks already live
  (`mirror_drift`, `last_log_age`), and a documented harness bug worked around
  (`hookdedup.py`).
- **`claude-persistent`** — demoted to an **optional VS Code viewer**. Rite ships and works
  without it. Its own docs still describe it as the product and will need correcting.
- **`project-tracker`** — a **consumer and producer** of the standard, not a subject of it.
  It owns portfolio scheduling; Rite owns the per-project contract. Boundary in DECISIONS
  `d-log-ownership-split`.
- **`ai-collab-interaction`** — holds `session-frame.yaml`, an unwired draft of the
  start-session protocol. Real prior art for Rite's second half.

## Response style

Bullets. Evidence-first — show the command output, not the claim. Say plainly what was NOT
done. No end-of-response summaries restating the diff.
