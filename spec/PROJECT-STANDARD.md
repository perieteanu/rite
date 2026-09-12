<!-- GENERATED FROM project-standard.yaml BY render-standard.py — DO NOT EDIT.
     Edit the YAML, then re-render: spec/render-standard.py
     Verify with:                   spec/render-standard.py --check -->

# The fully featured project

> What files a project must carry so that a cold agent, or a cold human, can pick it up without re-deriving it — and the checks that fail when one of them goes missing or stale.

**Version** `1.0.0` · **As of** `2026-09-07` · **Status** `draft`

## Why this exists

The practice existed for ~12.5 months across 50 projects and was never written down. The only prior declaration (ADR d-docs-yaml-self-documenting, 2026-04-24) was scoped to a single project, declared five files, and omitted the three that are actually universal. Everything else drifted: six naming schemes for one concept, five for another. A convention that is imitated rather than specified cannot be checked.

**Principle.** Prefer a check that fails over a discipline that must be remembered. Every artifact here declares completion tests for exactly that reason. A standard that passes everything is not a standard.

## Evidence base

| measure | value |
|---|---|
| span | 2025-08-22 to 2026-09-07 |
| sessions | 462 |
| prompts | 4864 |
| log entries | 1808 |
| projects with log | 50 |
| adrs | 230 |

Structure sampled from: `hwprivacy`, `astrolabe`, `project-tracker`, `api.pdf`, `plumbing`, `plan-evacuare`.

## Two layers

- **core** — Publishable. The artifact set, what question each answers, its required structure, and its completion tests. Independent of any one person's tooling.
- **local** — Machine-specific and configurable. Line formats, tag vocabularies, directory naming, and integration with a portfolio registry. Rite reads these from config; strangers override or ignore them.

**Stages.** `idea`, `spec`, `build`, `polish`, `shipped`, `maintain`, `archived`

Tier 1 becomes required at stage `None`.

## Tiers

| tier | label | rule | evidence |
|---|---|---|---|
| 0 | Always, from creation | Present at every stage, including idea. | 11/11 sampled projects carry README, CLAUDE.md and LOG.md, including the two carrying none of Tier 1. HANDOFF.md was promoted here by user ruling on 2026-09-07, against the corpus rather than from it: 0/11 carried one reliably, which is the gap, not the norm. |
| 1 | Once committed | Required once the project has committed. Since 2026-09-08 the trigger is the PRESENCE OF THE .rite.yaml MARKER, not a stage field: opting in IS the act of committing, so Rite needs no stage source to enforce Tier 1. This replaced "required from stage `spec` onward", which depended on knowing a stage Rite has no reliable way to read. | 9/11 sampled; adopted all-or-nothing, never partially. |
| 2 | Situational | Not required. When present, the canonical name and shape apply. | — |
| 3 | Generated | Written by tooling. Never hand-edited; edits do not propagate back. | — |

## Required provenance header

Required in every file in the docs directory — as YAML front matter in a .md, as top-level keys in a .yaml. One parser reads both, so the header is form-independent by design.
.

```yaml
schema_version: "1.0.0"
as_of: "YYYY-MM-DD"
status: draft | current | superseded
```

- **`schema_version`** — version of THIS file's own shape
- **`as_of`** — The date this file's claims were last verified against the thing they describe — the code, the host, the physical installation. NOT the date it was last edited. Touching a typo does not move as_of; re-checking the claims does.
- **`status`** — 

## File format

**Rule.** If a checker must read a FIELD of it, it is YAML. If a human reads it end to end, it is Markdown. Nothing is both.

| form | provenance header | structure unit | tested by |
|---|---|---|---|
| `md` | YAML front matter, fenced by --- at the top of the file | H2 heading (`## Name`) | `required_sections`, `no_empty_sections`, `min_content_sections` |
| `yaml` | top-level keys | mapping key | `required_keys_present`, `entry_required_keys`, `unique_ids`, `min_list_items` |
| `text` | none — and a header would be a defect | n/a — reproduced verbatim | `min_lines`, `no_provenance_header` |

This project's own spec exists in both forms with byte-identical content: 25287 bytes as YAML, 19275 as Markdown — 24% smaller — because YAML charges a `key:` and an indent for every line of prose. The saving reverses for genuinely structured data, where Markdown must reinvent nesting that YAML gives for free.

Markdown needs no parser, degrades gracefully, and cannot fail to load on a bad indent. YAML needs one — scripts/riteyaml.py, stdlib only, whose subset is declared below. That argues for Markdown everywhere EXCEPT where the alternative is hand-writing a Markdown-structure parser, which trades a small declared subset for a worse undeclared one. Hence the split rather than a single answer. CORRECTED 2026-09-12: this said "YAML needs PyYAML", which stopped being true on 2026-09-08 when d-stdlib-only-yaml-subset dropped the dependency. PyYAML is the differential test's ORACLE and is imported nowhere in the product.

## The YAML subset

**Rule.** Rite reads a deliberately small subset of YAML and REFUSES the rest rather than guessing. A refusal declares one of two kinds, because they are different facts about different things: `invalid` means the text is not YAML, which is the project's defect; `unsupported` means valid YAML using a construct outside this subset, which is Rite's limit.

One error class carrying both was tolerable while only Rite's own artifacts were parsed, and became wrong the moment every YAML file in a project was. Calling a working docker-compose broken because it uses an anchor is a false accusation; passing over a genuinely corrupt document because Rite cannot tell the difference is a silent wrong answer. So `invalid` is RED and names the construct, `unsupported` is YELLOW and names the construct, and neither is reported in the register of the other.

Re-measured 2026-09-11 across all 478 YAML files on this machine with PyYAML as oracle, and the numbers are the reason this section exists. TWELVE files the parser accepted are rejected by PyYAML — ten of them a plain scalar containing a colon and a space, read as text. SIX valid files were refused for a quoted scalar continued onto a second line. Both directions are fixed; after the fix, false accepts are ZERO and every remaining refusal of a PyYAML-valid file is one of the declared constructs below.

**Supported.**

- block mappings and block sequences, nested, including sequences of mappings
- plain, single-quoted and double-quoted scalars, INCLUDING quoted scalars continued across lines
- block literals and folded blocks, with strip and keep chomping indicators
- flow sequences and flow mappings, nested, wrapped across lines, with quoted values
- comments, one leading document marker, a trailing document end marker
- null, true, false, integers, floats
- a leading byte order mark, and CRLF line endings

**Refused — valid YAML outside the subset, reported YELLOW**

| construct | looks like | why |
|---|---|---|
| `anchor` | `&name` | An anchor names a node for reuse. Rite has no use for reuse inside a document it only reads once. |
| `tag` | `!!type` | A tag forces a type. Rite infers the types it supports and refuses to implement the rest. |
| `merge_key` | `<<:` | A merge key splices one mapping into another, so the document no longer says what it contains. |
| `complex_key` | `? key` | An explicit key may itself be a collection, which nothing in this standard has a use for. |
| `ambiguous_boolean` | `enabled: yes` | YAML 1.1 reads yes/no/on/off as booleans and YAML 1.2 reads them as strings. Guessing which one a reader meant is exactly what this parser refuses to do. Quote it, or write true/false. |
| `flow_set` | `{a, b}` | An entry with no colon is a set, not a mapping, and Rite would have to invent its values. |
| `multi_document` | `--- after content` | Valid as a STREAM. Rite reads one document per file everywhere, so the second was silently merged into the first until 2026-09-12 — 29 files on this machine. A file holding two documents is a file whose second half Rite would ignore. |
| `nested_list_under_plain_item` | `- a then a more-indented - b` | YAML folds it into the single string "a - b". It is valid and it is almost always a nested list whose parent key was forgotten, so it is reported rather than quietly turned into prose. |

**Rejected — not YAML at all, reported RED**

| construct | looks like | why |
|---|---|---|
| `mapping_value_in_plain_scalar` | `a: x: y` | A plain scalar cannot contain a colon followed by a space, or end in a colon. TEN of the twelve false accepts. |
| `unterminated_quote` | `a: "one` | A quoted scalar with no closing quote, or one whose continuation runs into a document marker. |
| `text_after_quote` | `a: "x" y` | A closing quote followed by more text is not a scalar and not a mapping. |
| `unterminated_flow` | `a: {b: 1` | A flow collection whose bracket never closes. |
| `bad_indentation` | `a key indented deeper than its siblings` | An over-indented key, or a sequence under a value that already ended. |
| `tab_indentation` | `a tab before content` | YAML forbids tabs in indentation. Accepted until 2026-09-12, and the document came out mis-structured as well — the worse half, because it read as a document that had parsed. |
| `content_after_root` | `a mapping, then a sequence, at column 0` | The top-level structure ends and the file keeps going. The reader used to return what it had and DROP the rest, so a truncated document read as a complete one. |
| `expected_key_value` | `a line in a mapping that is not a key` | Inside a mapping, a line that is neither a key nor a continuation of the value above it. |
| `undefined_alias` | `*name` | An alias with no anchor before it. Anchors are refused on sight, so reaching an alias proves no anchor was ever defined, which makes it unresolvable rather than merely unsupported. |
| `reserved_indicator` | `a: @x` | The characters @ ` % cannot start a plain scalar, and neither can a bare & or * with no name. |

**Which files are checked.** Every YAML file under the project's documentation directory, plus any glob the project declares in `.rite.yaml` under `yaml_check.include`, minus anything in `yaml_check.exclude`. A file that is also a declared artifact is checked once, by the artifact's own parse precondition, and never reported twice.

Where the project is a git repository, the files git knows about: tracked, plus untracked ones that are not ignored. Elsewhere, a case-exact filesystem glob. An ignored file is therefore not checked in a repository, which is deliberate — an ignored file is not part of what the project publishes about itself.

MEASURED 2026-09-11: of 65 ambiguous-boolean refusals across this machine, 62 are `on:` in GitHub workflow files — a dialect GitHub owns rather than the project, and one Rite has no standing to judge. The same is true of anchors in a compose file and tags in a CloudFormation template. The documentation directory is the ground this standard actually covers; anything further is the project's own declaration to make.

Broken YAML is broken at `idea`. The stage decides which DOCUMENTS a project is asked for, never whether the ones it has may be corrupt.

An include or exclude declared in .rite.yaml is reported as a counted line, the same rule threshold overrides follow. A narrowed scope that nothing states is a silent opt-out.

- **`yaml_parses`** (RED) — Every checked file is YAML, and a file that is not names the construct and the line.
- **`yaml_within_subset`** (YELLOW) — Every checked file stays inside the declared subset, naming the construct where it does not.

**Honest limits.**

- A file whose entire content is one bare scalar is valid YAML and is reported `invalid` (expected_key_value). Nothing in this standard is shaped that way, and the alternative is teaching the reader a document form it would never otherwise meet.
- A `%YAML` directive is valid and is reported `invalid`. Same reasoning, same trade.
- Values are read as YAML 1.2 where the two versions disagree: an unquoted date stays a string and `0600` is six hundred, not octal 384. This affects what a value MEANS, never whether the file parses, and the freshness rules parse dates themselves.
- `invalid` is riteyaml's judgement, not a YAML validator's. It is proven by the differential test against PyYAML for every construct declared above, and that is the whole of the claim — a construct nobody wrote a case for is a construct Rite may still get wrong.

## Write discipline

**Rule.** Every artifact declares exactly one. An artifact with no declared write discipline has no rule a check can test, which is the same as having no rule.

| value | means | hazard |
|---|---|---|
| `append_only` | Never rewrite existing content. Only add, at the end. | — |
| `rewrite_only` | States current truth. Stale content is DELETED, never annotated or accumulated. The file must be readable as a statement about now, with no archaeology in it. | Accumulation. A rewrite-only file that only grows has silently become append-only and stopped being true. |
| `write_once` | Frozen at a declared moment. Not appended, not rewritten, not regenerated afterwards. There is no source to regenerate it FROM — the file IS the record. | Editing one falsifies a record of what was actually agreed, and nothing detects it. |
| `free_replace` | Overwritten wholesale from a declared source. Local edits are discarded by design. | — |
| `mixed` | Entries mutate, but an id ledger inside the file is append-only. Must state which part is which. | — |

| artifact | write discipline |
|---|---|
| `CLAUDE.md` | `rewrite_only` |
| `HANDOFF.md` | `write_once` |
| `LOG.md` | `append_only` |
| `README.md` | `rewrite_only` |
| `docs/ARCHITECTURE.md` | `rewrite_only` |
| `docs/CONVENTIONS.md` | `rewrite_only` |
| `docs/DECISIONS.yaml` | `append_only` |
| `docs/MISSION.md` | `rewrite_only` |
| `docs/ROADMAP.yaml` | `mixed` |
| `LICENSE` | `write_once` |
| `docs/CONCERNS.yaml` | `mixed` |
| `docs/PLAN-YYYY-MM-DD-<slug>.md` | `write_once` |
| `docs/claude-memory.md` | `free_replace` |
| `docs/session-scripts/<ISO date>/<name>` | `write_once` |

## Verdicts and failure semantics

Vocabulary: `GREEN`, `YELLOW`, `RED`, `NA` · sides: `claude`, `project`, `machine`

Every finding is tagged whose-side-to-fix. This is preflight's one original idea and it carries over unchanged. For the project standard almost everything is `project`; `machine` and `claude` belong to the session-start checks.

| test level | severity | why |
|---|---|---|
| `exists` | **RED** | An artifact required at this tier is missing. Nothing else about the project can be trusted to be checkable. |
| `populated` | **YELLOW** | The file is there but empty, placeholder-filled, or missing a required section. A defect, not a void. |
| `fresh` | **YELLOW** | It was true once and is not now. Staleness is advisory by nature — treating it as fatal makes the gate fire constantly. |
| `integrity` | **RED** | Something is actively WRONG, not merely old: an append-only file was rewritten, a supersedes id resolves to nothing, a generated file no longer matches its source. These are the checks that catch a lie rather than a lapse. |

- `exists` — A tier-2 artifact that is absent is NA, not RED — optional means optional.

**Exit policy.** exit 1 on any RED; YELLOW and GREEN exit 0 — `fail_on: red | yellow | none`

So the gate stays credible. A check that breaks the build every time a document is slightly old is the gate that always fails, and it gets switched off within a week — the argument this project makes about everything else, applied to itself.

A non-zero exit is what lets Rite gate a pre-commit hook or a CI run. That is the strongest enforcement available to it, and refusing to ever fail would give it up.

**Never blocks a session.** Verdicts are REPORTED at session start, never enforced there. The start phase already declares must_not: block, prompt, or re-run anything with side effects. Gating belongs to an explicitly invoked checker, not to a hook the user did not ask for.

## Participation

Model `opt_in` · marker `.rite.yaml`

Rite checks a project ONLY if the marker is present. Everywhere else it is silent — no verdict, no nag, no first-run prompt.

Migration of existing projects is explicitly opt-in (d-audience-public-standard, and the standing don't-migrate rule). A tool that starts reporting on 40 projects nobody asked it to check is noise on first contact, and noise is what gets a plugin uninstalled.

`.rite.yaml` is CONFIG, not a documentation artifact, so it does not count against the inventory frozen at 13. The inventory covers what a cold human or agent READS to understand the project; this file is operational, in the same family as .gitignore or phpstan.neon. Recorded explicitly because the freeze exists precisely to stop additions being absorbed without argument — see d-verdicts-and-participation.

- minimal: an empty file is a valid marker — presence is the signal
- optional keys: `standard_version`, `fail_on`, `thresholds`, `disabled_checks`, `yaml_check`, `source_exclude`

### Thresholds

**Rule.** Freshness windows are per-project overridable. Structural minimums are NOT. The two are different kinds of number and conflating them would let a project define away the standard.

| overridable | default |
|---|---|
| `log.newest_entry_within_days_of_activity` | 30 |
| `roadmap.as_of_within_days_of_activity` | 60 |
| `architecture.as_of_within_days_of_activity` | 90 |

All three are admitted guesses, never calibrated against a real corpus (c-freshness-thresholds-are-guesses), and project cadence genuinely varies. `plumbing` changes twice a year; a fixed 60-day roadmap window would fail it permanently and teach the user to ignore the tool.

**Fixed, not overridable:** `min_lines`, `min_entries`, `min_content_sections`, `min_list_items`, `required_sections`, `required_keys_present`, `required_from_stage`

These ARE the standard rather than a calibration of it. A LOG with zero entries is broken regardless of taste, and a project that can lower every bar to its own current state is not being measured by anything.

**Overrides are never silent.** Any finding computed with an overridden threshold MUST report the override and the default alongside it — e.g. "roadmap as_of 210d old (window 365d, overridden from 60)".

An unbounded override is a silent opt-out: set 99999 and the check never fires again, with nothing to show it was ever disabled. There is deliberately NO cap, because any cap would be as arbitrary as the default it protects. Visibility is the control, not a limit — the same principle as "explicit nothing beats absent". A project may widen a window; it may not do so invisibly.

A check silenced via `disabled_checks` is reported as NA with "disabled in .rite.yaml", never omitted from the output. A check that vanishes and one that passed must never look alike.

## Capabilities

**Prerequisite — `python3`.** Needed for every script — preflight, the checker, the memory mirror, plan copy.

_Not needed for: the judgement half. /end, /log and /handoff are Markdown prompts._

**Capability, not prerequisite — `git`.**

- enables: `append_only_preserved`, `milestones_append_only`, `inception_unchanged`, `content_stable_after_creation`
- when absent: those tests report NA — requires revision history. Never RED, never silently omitted.
- why not required: MEASURED 2026-09-08 across 10 sampled projects: SIX are not git repositories, including `plumbing` and `usa-beci` — the two non-code projects d-noncode-first-class explicitly promises to serve — plus project-tracker, claude-preflight, claude-persistent and rite itself. Requiring git would fail 60% of the corpus and break a settled ADR.
- expectation: On most of this machine's projects the integrity tier will read NA. The useful coverage for them is exists / populated / fresh. Know that before building the checker rather than discovering it at validate-against-real-projects.

| available | what works |
|---|---|
| neither python nor git | the ENTIRE judgement half — /end, /log, /handoff. Markdown prompts; no interpreter. |
| python, no git | + preflight verdict, exists / populated / fresh checks, memory mirror, plan copy |
| python and git | + the integrity tier |

A CONSEQUENCE, not a selling point. The expected consumer runs Claude Code and almost certainly has both python and git already, so Rite states "Requires Python 3" plainly and does not advertise degradation — d-goal-is-credibility rules out over-engineering toward installs. This tier costs nothing to keep because it was never built: the judgement half needs no interpreter as a consequence of commands being Markdown prompts. It is what the setup check REPORTS when reality differs from the expectation.

### The setup check

**Purpose.** Report which capabilities are present and what each one enables. Nothing else.

**`never_instruct_installation`** — Rite MUST NOT tell a user to install anything, and MUST NOT print a command to paste. It reports what is present, what is dormant, and what that costs.

_Why: The tool cannot see the machine's existing state — system python, pyenv, conda, the Microsoft Store alias, WSL, Git Bash's own interpreter — so any install instruction is a guess with the user's environment as the stake. A wrong guess breaks a working setup, and the user then owns a problem the tool created._

_Instead: Name what is missing and what is unavailable because of it. If the user asks how to fix it, link the vendor's own documentation; never a command._

**`never_modify_the_environment`** — Never install, never edit PATH, never write to a python, pyenv or git config. Ever.

_Why: Extends never_mutate_claude_home to the whole machine. Detection is read-only by construction._

**`probing_must_not_trigger_installs`** — On Windows, do NOT invoke bare `python` to test for it. The App Execution Alias opens the Microsoft Store.

_Why: The DETECTION would itself cause the surprise it is meant to prevent — a Store window appearing because a background check ran. Probe with `py -0` or by resolving the executable path instead of executing it._

**`three_states_not_two`** — Report absent / present-but-broken / working. They are different problems and need different words.

_Why: A broken interpreter is the worst state and the most confusing: something IS installed, so 'install Python' is wrong advice and will send the user to make it worse. Detect by running a trivial program, not by finding a file._

_Wording: Absent -> 'not found; the mechanical half is unavailable'. Broken -> 'found at <path> but it fails to run'. State the path, state the symptom, prescribe nothing._

**`pull_not_push`** — The setup report is available on request. It is not shown unprompted more than once.

_Why: Same argument as the nag policy and the rejected timer reminders: a message that is always true stops being read._

## Inventory freeze

**13 artifacts, frozen 2026-09-07.** Human-authored artifacts only. Files PRODUCED BY SCRIPTS are deliberately out of this freeze and are specified separately, once their producers exist and their purpose is settled. An artifact whose producer does not exist cannot be specified honestly — its shape is guesswork dressed as a standard.

_Exception — `memory_mirror`: docs/claude-memory.md is script-produced yet declared here, because its producer already exists and runs (claude-mirror-memory.py, a PostToolUse hook). Consistent with the rule rather than an exception to it: a generated artifact is declarable exactly when its producer is real._

| candidate | what | status |
|---|---|---|
| `status_json` | The SessionStart verdict — machine / project / claude | deferred — necessity not yet agreed |
| `checks_yaml` | Config driving the session POST, inherited in shape from claude-preflight | RESOLVED 2026-09-10 — exists, and is NOT an artifact |
| `end_stamp` | A marker that /end ran | REJECTED — not deferred |

- **`status_json`** — Discussed 2026-09-07 and NOT added. The need is asserted, not established.
- **`checks_yaml`** — The deferral asked what it must contain for a stranger versus for this machine. Answered by building it. It lives at ${CLAUDE_PLUGIN_DATA}/checks.yaml — plugin storage, which never_mutate_claude_home names as its one declared exception, and where the nag-once mechanism already lives. It configures the MACHINE and the AGENT, not a repository, so a per-project copy would be the wrong shape and the inventory stays at 14. template/checks.yaml is the documented default, carrying no machine-specific values. What is "for this machine" needs no answer from the standard after all: a check whose config carries a `command:` runs an external program, so anything too personal to publish lives in the user's config and never in the engine.
- **`end_stamp`** — Ruled out 2026-09-07: /end is a process, and its result is recorded in HANDOFF.md front matter (`session_end:`). No new file. This is why the standard has 13 artifacts and not 14, and the rejection is recorded so it is not helpfully re-proposed.

## Portability

Targets: `linux`, `macos`, `windows`

VS Code and the terminal differ MORE than Windows and macOS do, but not for file handling — only for what a hook can surface. Under entrypoint=claude-vscode only `additionalContext` reaches the session (systemMessage/showOutput do nothing, re-verified on 2.1.263), and the /plugin TUI is unavailable, so installation must go through the `claude` shell CLI. Design output for additionalContext as the lowest common denominator. None of this affects YAML, Markdown, or any check.

| rule | severity | what |
|---|---|---|
| `case_sensitive_name_matching` | correctness | NEVER use Path.exists() to test for an artifact. List the directory and compare names exactly, byte for byte. |
| `generated_output_is_lf_only` | correctness | Every generated file is written with newline="\n". Never the platform default. |
| `normalize_before_byte_comparison` | correctness | Any test comparing a file against a previous revision normalizes line endings first. Compare content, never encoding of line breaks. |
| `process_output_declares_encoding` | correctness | Every entry point declares its stdout and stderr as UTF-8 before printing, via ritefs.use_utf8_stdio(). Every read of another process's output names BOTH encoding="utf-8" AND errors="replace". A byte must not mean different things at the two ends of one pipe. |
| `shell_only_as_a_launcher` | correctness | Shell is permitted in exactly ONE place: a launcher shim that locates Python or explains why it cannot. Nothing else. No checks, no parsing, no logic. |
| `explicit_utf8_everywhere` | correctness | Every read and write names encoding='utf-8'. Never rely on the platform default. |
| `python_invocation_differs` | documentation | Never hardcode `python3` in documentation or a hook command. On Windows the name is `py` or `python`; `python3` is not a standard Windows executable. |
| `stdlib_only_no_pip_dependencies` | correctness | Python stdlib only. No pip install, ever, for the base layer. YAML is read by a subset parser shipped with Rite. |
| `claude_home_slug_derivation` | documentation | Derive root -> slug and never slug -> root. The first is deterministic and governs every write; the second is lossy and may only name a project in a report. |

**`case_sensitive_name_matching`** — macOS (APFS default) and Windows are case-insensitive. Path("README.md").exists() returns True for a file actually named readme.md. A project carrying readme.md and Claude.md therefore PASSES on macOS and Windows and FAILS on Linux — the same repo, two verdicts. For a standard whose entire value is canonical names, that is a correctness bug, not a portability nicety. It is also the rule most likely to be undone by a well-meaning simplification.

**`generated_output_is_lf_only`** — write_text() with no newline argument translates \n to os.linesep, so a file generated on Windows lands as CRLF. The drift gate itself survives, because text-mode reads normalize — but the file churns byte-wise across platforms and a diff shows every line changed. Applied to render-standard.py on 2026-09-07.

**`normalize_before_byte_comparison`** — VS Code on Windows saves CRLF by default. PyYAML parses \r\n without complaint, so DECISIONS.yaml still loads — but append_only_preserved compares bytes, and every line reads as changed. The integrity test would fail on a file nobody touched.

_Rejected alternative: A .gitattributes with eol=lf. Correct, conventional, and rejected: it is a hand-authored 14th file one hour after the inventory was frozen at 13. Normalizing inside the comparison achieves the same result with no new file, consistent with the ruling that put the /end outcome in HANDOFF rather than a stamp._

**`process_output_declares_encoding`** — The existing rules cover files. This one covers PIPES, and its absence was found on 2026-09-10 by the first CI run that was not on Linux. Python selects the console codepage for stdout on Windows, so a report containing `·` or `—` is emitted as cp1252 there and as UTF-8 on Linux and macOS — one program, three byte streams. run-gates.py captured a child with encoding="utf-8", got cp1252, and a reader thread died with `UnicodeDecodeError: ... byte 0x97`, which is cp1252's em dash. TWO gates reported FAIL for a reason having nothing to do with what they test — the worst kind of red, because it accuses the wrong component.

_Rejected alternative: ASCII-only output. It would need no declaration at all, and it is not available: the messages are read from YAML documents that are full of em dashes, so the text is non-ASCII before any code formats it. The encoding has to be stated, not avoided._

**`shell_only_as_a_launcher`** — The shell is the only executor guaranteed to exist — but it is not portable, because .sh and .bat are two implementations. "Guaranteed present" and "written once" are mutually exclusive, and this rule takes both, by making the guaranteed-but-duplicated part as small as it can possibly be.

**`explicit_utf8_everywhere`** — Windows defaults to cp1252. The generated standard contains 171 non-ASCII characters (em dash, middle dot, left arrow), and YAML mandates UTF-8 regardless of platform. An unqualified open() works on Linux and corrupts on Windows, which is the worst possible failure ordering — it passes where it is developed.

**`python_invocation_differs`** — The command printed in a README is the first thing a new user runs, and on Windows this one fails.

**`stdlib_only_no_pip_dependencies`** — PyYAML is not installed by default on macOS or Windows, so depending on it would make "pip install first" the default first-run experience on two of three target platforms. Measured across 1839 lines of this project's own YAML, every construct that makes YAML hard to parse is unused — no anchors, aliases, tags, flow mappings, block literals, merge keys or complex keys — so the dependency buys almost nothing.

**`claude_home_slug_derivation`** — Memory directories encode the project path with every non-alphanumeric character replaced by a dash (-home-perieteanu-projects-rite). On Windows that is a drive letter and backslashes, encoded the same way.

## The artifact set

| tier | path | answers |
|---|---|---|
| 0 | `CLAUDE.md` | What must an agent know before touching this? |
| 0 | `HANDOFF.md` | What must the next session know that the docs do not say? |
| 0 | `LOG.md` | What happened, in order? |
| 0 | `README.md` | What is this, and how does a human start? |
| 1 | `docs/ARCHITECTURE.md` | What lives where, what flows where, and who owns what? |
| 1 | `docs/CONVENTIONS.md` | What formats and vocabulary does this project use? |
| 1 | `docs/DECISIONS.yaml` | What is settled, and must not be re-litigated? |
| 1 | `docs/MISSION.md` | Why does this exist, and what is it deliberately not? |
| 1 | `docs/ROADMAP.yaml` | What is next, what is deferred, and how do I restart cold? |
| 2 | `LICENSE` | Under what terms may this be used? |
| 2 | `docs/CONCERNS.yaml` | What is proposed or worrying but NOT yet settled? |
| 2 | `docs/PLAN-YYYY-MM-DD-<slug>.md` | What was the agreed plan for a piece of work? |
| 3 | `docs/claude-memory.md` | What does the agent durably remember about this project? |
| 3 | `docs/session-scripts/<ISO date>/<name>` | How was this change actually made? |

## Artifacts in detail

### `CLAUDE.md`

**Tier 0** · layer `core` · audience `agent` · form `md` · write `rewrite_only`

**Answers:** What must an agent know before touching this?

**Recommended sections:** `What this is`, `Read first (in this order)`, `The one insight the whole project rests on`, `Traps that produce plausible-but-wrong output`, `Don'ts / firm rules`, `Locked findings (do not re-litigate)`, `Explicitly NOT built yet`, `Relationships`, `Response style`

**Notes.** `Don'ts` appeared in every sampled project and is the load-bearing section. `Explicitly NOT built yet` and `Locked findings` are what stop a fresh session re-doing settled work; both are cheap and both are usually missing.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `required_sections` | `['What this is']` |
| populated | `min_lines` | `15` |
| populated | `claims_declared` | This document declares a `claims:` block. A core document that asserts nothing falsifiable about the tree is not wrong — it is unfalsifiable, which is worse, because it cannot be caught being wrong either. |
| integrity | `claims_match_filesystem` | Every path in `claims.absent` is absent and every path in `claims.present` is present. This is the api.pdf doc-rot class: a claim that reads perfectly and is flatly wrong. INTEGRITY rather than fresh — a document that is confidently wrong is not merely stale, and the level is what decides whether the verdict is loud. LIMIT: path-shaped claims only. A claim about BEHAVIOUR ("it writes status.json") passes untouched. |

### `HANDOFF.md`

**Tier 0** · layer `core` · audience `agent` · form `md` · write `write_once`

**Answers:** What must the next session know that the docs do not say?

**Genres:**

- **`state`** — Where things stand mid-work. Sections: pick up here, what is running, traps, deliberately not done.
- **`prompt`** — A literal copy-paste block to open the next session with, plus commentary outside it.
- **`task_brief`** — A scoped assignment: goal, parts, definition of done, already-settled list.
- **`none`** — An explicit statement that there is nothing to hand off, and why — work closed cleanly, or the next step is fully described by ROADMAP near_term. This is a REAL answer and it passes. It is not the absence of a handoff; it is the assertion that none is needed, made by someone who considered the question.

**Required frontmatter:**

```yaml
genre: one of the ids above
written: YYYY-MM-DD
expires: YYYY-MM-DD — a DATE, always. Required.
status: live | spent
session_end: written | updated | carried_forward | none — the outcome the closing session recorded
```

**Expiry rule.** MANDATORY, and the clearest gap this standard closes. No HANDOFF in the entire sampled corpus carried any expiry, spent, consumed or valid_until marker. The failure is live today: claude-persistent/HANDOFF.md is described as "spent" in a sibling file and still sits in the project root reading as authoritative. A spent handoff is worse than no handoff, because it is confidently wrong.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `required_frontmatter_present` | — |
| fresh | `not_expired` | status:spent or a past `expires` date must fail, loudly, and name the file. |
| integrity | `session_end_decision_recorded` | The last session closed with one of the four outcomes, declared in this file's own front matter as `session_end`. NO separate stamp file: the outcome is recorded here, by user ruling on 2026-09-07, specifically to avoid inventing a file for it. |
| integrity | `written_not_older_than_newest_log_entry` | **session-scoped.** This is what makes the previous test real without a stamp. A session that worked and then closed without touching the handoff leaves `written:` older than the newest LOG.md entry — detectable from two files that already exist. "Nobody thought about it" and "someone decided none was needed" are no longer indistinguishable: the first leaves a stale date, the second leaves a current one saying so. |

### `LOG.md`

**Tier 0** · layer `core` · audience `both` · form `md` · write `append_only`

**Answers:** What happened, in order?

**Notes.** The durable record. Transcripts are pruned by the harness — measured on this machine, four weeks of transcripts against ten months of LOG. The log outlives the session that produced it, which is the whole argument for writing one.

**File order vs timestamp.** File order is insertion order and MAY differ from chronological order. Any consumer must sort by parsed timestamp before displaying, ranking, or aggregating.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `min_entries` | `1` |
| populated | `entries_parse` | — |
| integrity | `no_future_timestamps` | **local_clock-scoped.** Every non-blank, non-heading line matches the configured line format. |
| fresh | `newest_entry_within_days_of_activity` | `30` — Code changed since the last log entry means the session did not close. |
| integrity | `append_only_preserved` | Existing entries are byte-identical to the previous revision. Only additions are legal. Format migrations are the sole exception and must be logged as such. |

### `README.md`

**Tier 0** · layer `core` · audience `human` · form `md` · write `rewrite_only`

**Answers:** What is this, and how does a human start?

**Recommended sections:** `What this is (one paragraph, no preamble)`, `Status — stage, and one line of current state`, `Install / run`, `Credits`

**Notes.** For a published project this is what the listing renders, so it is the highest-value file in the repo and the one most often left stale. README quality outweighs install counts for a portfolio artifact.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `min_lines` | `8` |
| populated | `no_placeholders` | `TODO`, `FIXME`, `<fill`, `XXX`, `Lorem ipsum` |
| populated | `claims_declared` | — |
| integrity | `claims_match_filesystem` | — |

### `docs/ARCHITECTURE.md`

**Tier 1** · layer `core` · audience `both` · form `md` · write `rewrite_only`

**Answers:** What lives where, what flows where, and who owns what?

_Schema strictness: loose._

**Required section — at least one of:** `Shape`, `Summary`, `Layout`

**Recommended sections:** `Hard boundaries`, `Rejected`, `Dependencies`, `Data flow`

**Canonical section, and the names it replaces:**

- `Shape` ← `Summary`
- `Hard boundaries` ← `Ownership rules`, `State ownership`

**Notes.** DELIBERATELY the loosest schema in the standard. It was the least standardized file in the corpus, and one sampled project's ARCHITECTURE is a physical plumbing topology (supply_chain, valves, loss_budget) rather than software. A required-key set narrow enough for both is the correct design; pretending to a tight schema here would only produce ceremonial compliance. `rejected` — designs considered and refused, with why — is what prevents a later session re-proposing something already ruled out.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `min_content_sections` | `3` — At least three H2 sections beyond the title. This replaces a required-key list, which cannot span a Rust codebase and a plumbing schematic. |
| populated | `required_any_of_sections` | One of the topology sections, honouring `section_aliases` — "Summary" satisfies "Shape". DECLARED 2026-09-10: the rule had been implemented since the checker was written and invoked by NOTHING, because `required_any_of_sections` appeared only under `structure:` as data and no artifact listed it under `tests:`. Dead code in the checker whose whole subject is rules nobody runs. YELLOW, never RED, and `required_any_of_waived_when` says why: a non-code project whose top-level keys ARE the topology has no generic container section, and d-noncode-first-class makes those first-class. The finding names the waiver so a reader can dismiss it deliberately rather than wonder. |
| fresh | `as_of_present` | — |
| fresh | `as_of_within_days_of_activity` | `90` — Measured against what the project last RECORDED as changed — see source_definition — never against another document. It said "source mtime" until 2026-09-12, which was both the implementation and the defect. |
| populated | `claims_declared` | — |
| integrity | `claims_match_filesystem` | The must_be_current artifact, and the one that rotted hardest. On 2026-09-08 it omitted the checker entirely; on 2026-09-09 it still called the session-start script "planned", said it writes status.json, and said it reads an /end stamp file that d-end-outcome-recorded-in-handoff had REJECTED — a rejected design documented as live, beside working code. |

### `docs/CONVENTIONS.md`

**Tier 1** · layer `core` · audience `both` · form `md` · write `rewrite_only`

**Answers:** What formats and vocabulary does this project use?

**Required sections:** `Naming`

**Recommended sections:** `File format`, `Language`, `Logging`, `Testing`, `No hardcoded values`, `Append-only`, `Vocabulary`

**Canonical section, and the names it replaces:**

- `Naming` ← `App naming`, `Naming rules`

**Notes.** Required in the core set: the evidence shows the five are adopted as a unit, and splitting them risks breaking the habit that made them stick. Where a project has no rules of its own beyond the global ones, this file should say exactly that in one line rather than sit empty — an explicit "nothing project-specific" is a real answer and passes; an empty file does not.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `required_sections` | — |
| populated | `no_empty_sections` | — |
| fresh | `as_of_present` | — |

### `docs/DECISIONS.yaml`

**Tier 1** · layer `core` · audience `both` · form `yaml` · write `append_only`

**Answers:** What is settled, and must not be re-litigated?

**Entry shape:**

- _required_ — `id`, `date`, `decision`
- _recommended_ — `title`, `context`, `rationale`, `consequences`, `status`
- _provenance_ — `proposed_by`, `confirmed_by_user`, `stated_by_user`
- _lifecycle_ — `supersedes`, `superseded_by`, `revisit_when`, `reconstructed`, `superseded_advice`

**Correction discipline.** Never edit a past entry. Append a dated correction block to it instead (e.g. `measured_reality_2026_08_04:`). This applies append-only WITHIN an entry, and is already practiced in two sampled projects.

**Staging area.** Unsettled proposals do not belong in DECISIONS. They go in a declared staging file (CONCERNS.yaml) or an `open:` section. Two projects invented this independently — convergent invention, so it is canonized rather than left to taste. Canonical path: `docs/CONCERNS.yaml`.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `min_entries` | `1` |
| populated | `entry_required_keys` | — |
| populated | `unique_ids` | — |
| integrity | `append_only_preserved` | — |
| integrity | `no_dangling_supersedes` | Every `supersedes` / `superseded_by` id resolves to an entry in this file. |
| fresh | `as_of_present` | — |

### `docs/MISSION.md`

**Tier 1** · layer `core` · audience `both` · form `md` · write `rewrite_only`

**Answers:** Why does this exist, and what is it deliberately not?

**Required sections:** `Mission`, `Constraints`, `Non-goals`

**Recommended sections:** `The key insight`, `Motivation quotes`, `Evidence base`, `Honest limit`

**Canonical section, and the names it replaces:**

- `Non-goals` ← `Explicit non-goals`, `Scope`

**Notes.** `non_goals` is the highest-value key and the most often skipped: it is what stops a later session drifting into adjacent rewrites. `motivation_quotes` — verbatim user quotes — survives paraphrase drift better than any summary.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `required_sections` | — |
| populated | `no_empty_sections` | — |
| fresh | `as_of_present` | — |

### `docs/ROADMAP.yaml`

**Tier 1** · layer `core` · audience `both` · form `yaml` · write `mixed`

**Answers:** What is next, what is deferred, and how do I restart cold?

**Required keys:** `inception`, `current_state`, `near_term`, `if_revisiting_cold`

**Recommended keys:** `mid_term`, `long_term`, `deferred_deliberately`, `milestones`

**Canonical key, and the names it replaces:**

- `current_state` ← `current_stage`
- `near_term` ← `next_up`, `milestones`
- `if_revisiting_cold` ← `what_to_do_if_revisiting_cold`, `revisiting_cold`, `cold_restart_checklist`

**Cold-restart shape.** An ordered list of imperative strings, conventionally ending with a "do NOT re-litigate X" line.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `required_keys_present` | — |
| populated | `min_list_items` | `if_revisiting_cold` `2` |
| populated | `inception_present` | A project with no recorded founding intent has no baseline; drift is unmeasurable from the first edit. |
| integrity | `inception_unchanged` | The `inception` block is byte-identical to its first committed form. This is the write-once zone of a mixed file, and it is the one people tidy without noticing. |
| fresh | `as_of_present` | — |
| fresh | `as_of_within_days_of_activity` | `60` — A roadmap staler than the code is the most misleading file in the set. |
| integrity | `deleted_ids_appear_in_milestones` | Every near_term `id` present in the previous revision and absent from this one must appear as a `milestones` entry. This is what makes deletion safe rather than lossy — the item is not erased, it is promoted. |
| integrity | `milestones_append_only` | The append-only half of a mixed file. Existing entries stay byte-identical. |
| integrity | `no_done_markers` | A near_term item carrying done/completed/finished status is a rewrite-only file being used as an append-only one. Delete it and log it instead. |
| populated | `claims_declared` | — |
| integrity | `claims_match_filesystem` | ROADMAP owns `current_state`, so it owns the project's most consequential claim about its own tree — and on 2026-09-09 that claim read "Still NO hooks, commands or skills. Not a git repo." against a running plugin in a repo with ten commits. The claims block is what makes the sentence testable; the sentence itself stays prose. |

### `LICENSE`

**Tier 2** · layer `core` · audience `human` · form `text` · write `write_once`

**Answers:** Under what terms may this be used?

**Notes.** Tier 2 rather than tier 0 because most tracked projects are private and never publish. It becomes required at stage `shipped`, which means a project that publishes without one FAILS — visibly, by design. Rite itself currently fails this check, and that is left visible rather than papered over.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `file_present` | — |
| populated | `min_lines` | `5` |
| integrity | `no_provenance_header` | A provenance header in LICENSE is a defect, not a compliance win. |

### `docs/CONCERNS.yaml`

**Tier 2** · layer `core` · audience `both` · form `yaml` · write `mixed`

**Answers:** What is proposed or worrying but NOT yet settled?

**Top-level keys:** `concerns`, `retired_ids`

**Entry shape:**

- _required_ — `id`, `title`, `status`
- _recommended_ — `severity`, `what`, `blocks`, `proposal`, `opened`

**Notes.** The staging area that keeps DECISIONS honest. Without it, unsettled proposals either pollute DECISIONS (and get treated as settled) or vanish.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `optional` | — |
| populated | `entry_required_keys` | — |
| populated | `unique_ids` | — |

### `docs/PLAN-YYYY-MM-DD-<slug>.md`

**Tier 2** · layer `core` · audience `both` · form `md` · write `write_once`

**Answers:** What was the agreed plan for a piece of work?

**Canonical name:** `PLAN-<ISO date>-<kebab slug>.md`

**Notes.** Plans are written outside the project, in a directory the workspace cannot see, under harness-generated names carrying no project attribution (e.g. cheeky-seeking-clock.md). They are lost when the session ends unless copied. Two of eight plans on this machine had been manually renamed to add the project — a workaround for exactly this gap.

**Attribution problem.** Memory directories encode the project in their path; the plans directory does not. Recovering plan -> project therefore needs mtime/session correlation or content inspection. This is the only genuinely hard part of automating the copy.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `optional` | — |
| populated | `filename_matches_canonical` | — |
| fresh | `source_plans_all_copied` | A plan in ~/.claude/plans attributable to this project with no copy here fails. |

### `docs/claude-memory.md`

**Tier 3** · layer `local` · audience `human` · form `md` · write `free_replace`

**Answers:** What does the agent durably remember about this project?

**Notes.** Functional source stays in ~/.claude/projects/<slug>/memory/. This mirror exists because a workspace rooted at the project cannot reach ~/.claude, which makes agent memory unauditable from the repo. Edits here do not propagate back.

**Generated by.** `claude-mirror-memory.py (PostToolUse hook)` — read-only, edits do not propagate back.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `optional` | — |
| fresh | `mirror_not_stale` | Newest memory file newer than the mirror's last sync fails. |

### `docs/session-scripts/<ISO date>/<name>`

**Tier 3** · layer `local` · audience `both` · form `text` · write `write_once`

**Answers:** How was this change actually made?

**Canonical name:** `session-scripts/<ISO date>/<original filename>`

**Notes.** The throwaway scripts a session writes to do its own work — the ones that performed the edits behind a commit. They live in /tmp, so they do not survive a reboot: late is the same as never, which is why this runs from SessionEnd as well as /rite:end. Attribution is free, unlike plan_copy: the scratchpad path already contains the project slug, so nothing has to be inferred. Deliberately narrow about what counts — *.py and *.sh at the scratchpad root only. The session that built this had a README.md.bak and a shipped-probe/ tree in the same directory, and neither is a script.

**Completion tests:**

| level | rule | detail |
|---|---|---|
| exists | `optional` | — |
| populated | `filename_matches_canonical` | — |

## Explicitly out of scope

Named boundaries, so a later session does not re-litigate them.

**`evolution`** — `docs/*-EVOLUTION.yaml` (owner: `project-tracker`)

It answers "what can I tackle tonight?" — a portfolio and scheduling question, not "what must an agent know before touching this project?". Its schema confirms it: lanes, nodes, edges, branches, progress, slippages is a timeline-renderer format. It is the only file in the corpus with a fully declared schema and it belongs to a different product. Rite neither requires, folds, nor renames it.

_Its `vocabulary:` enum block stays with project-tracker too. Rite defines its own stage_vocabulary above precisely so tiering does not depend on a registry a stranger will not have._

**`portfolio_registry`** — `projects.yaml, next-steps.yaml, show-portfolio, seed-projects` (owner: `project-tracker`)

project-tracker answers "what should I touch tonight?" — cross-project scheduling, ranked by cognitive mode rather than difficulty. Rite answers "did this session close properly?" for ONE project. Different questions, different scopes, different lifetimes. A per-project standard cannot depend on a cross-project registry a stranger will not have.

**`self_profiling`** — `ai-collab-profile/, ai-collab-interaction/, prompts.db, prompts-corpus.jsonl` (owner: `Costin — personal`)

A longitudinal profile of how Costin works with Claude: 4864 prompts, 462 sessions, 2.72M characters of his own words. It is a THIRD goal, distinct from both scheduling and session discipline, and it is his alone.

**`session_protocol`**

The session start/end protocol is Rite's companion piece and gets its own spec. This document defines the TARGET STATE; the protocol defines when it is written.

## Local layer (configurable — not part of the public standard)

Everything below is this machine's convention. Rite reads it from config; anyone else overrides or ignores it.

**`docs_dir`**

- `default` — docs
- `alternatives` — `docs-yaml`, `doc`, `documentation`
- `note` — Format-neutral by rule. A directory named for a file format becomes a false claim the moment one file inside it changes form — the exact class of stale statement Rite exists to catch. Renamed docs-yaml -> docs on 2026-09-07 for that reason.

**`log_line_format`**

- `format` — DD-MM-YYYY HH:MM[:SS] | DDD | <short_name> | [TYPE] <description>
- `seconds` — OPTIONAL, added 2026-09-08. Additive rather than a migration: minute-precision entries remain valid and are re-emitted byte-identically, so no append-only exception is needed. Parsers must accept both forms and PRESERVE the precision they read — re-emitting a minute entry with :00 would be a mass rewrite of 1800+ append-only lines.
- `why_seconds` — The previous convention required entries from one session to be at least a minute apart, which mandates inventing spacing whenever several things happen in the same minute. That rule produced roughly thirty fabricated timestamps on 2026-09-07. Seconds let entries be simply true, so the spacing rule was deleted rather than obeyed.
- `date_order` — European — deliberate, matches locale
- `day_of_week` — English 3-letter, fixed width, locale-independent
- `generation_warning` — System locale is ro_RO; `date +%a` emits 'Jo', 'Lun'. Force English with LC_ALL=C.
- `tag_vocabulary` — `work`, `note`, `fix`, `decide`, `pivot`, `add`, `defer`, `drop`, `done`

**`registry`**

- `source` — ~/projects/project-tracker/projects.yaml
- `provides` — `stage`, `status`, `short_name`, `group`
- `absent_behavior` — stage falls back to inference; registry-dependent checks skip

- **`timestamp_discipline`** — Always the machine clock, read PER ENTRY — never extrapolated from an earlier reading. Never invent, round, or approximate. There is no minimum spacing: entries carry the time they were written even when several share a second, and ties are broken by file order.
