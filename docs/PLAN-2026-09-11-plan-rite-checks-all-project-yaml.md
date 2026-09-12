<!-- Copied from ~/.claude/plans/valiant-spinning-sedgewick.md on 2026-09-11.
     Plans are written outside the project under harness-generated names carrying no
     project attribution; they are lost when the session ends unless copied. Canonical
     name per spec/project-standard.yaml artifact `plan_copy`. Copied by rite_copy.py,
     which attributes a plan to the project whose SESSION wrote it. -->

# Plan — Rite checks all project YAML against a declared subset

## Context

A documents-only project adopted Rite (peugeot307sw, 2026-09-10) and committed broken YAML twice.
Both files (`docs/WORKLIST.yaml`, `docs/FAULTS.yaml`) sit outside Rite's artifact inventory, so
`rite check` scored 0 RED. `parse_failure()` in `scripts/rite-check.py:908` only ever runs on
inventory artifacts. Costin ruled 2026-09-11: **check them** — extend the parser or limit the
YAML by declaring it. Harvested as `c-project-yaml-is-not-checked` (docs/CONCERNS.yaml).

Measured before designing (riteyaml vs PyYAML over 478 files on this machine, plus probes):
- Both real breaks are refused, the valid file accepted — the parser CAN do this job.
- 22 files are invalid today, all rejected.
- **False accepts (PyYAML rejects, riteyaml accepts) — must reach zero before shipping:**
  plain scalar containing `: ` or ending in `:` (10 in the corpus); `*`/`&` not followed by a
  name (`- *.log`); a value starting with `@` or backtick; tab indentation (accepted AND
  mis-structured); a mid-file `---` (two documents silently merged); root mapping followed by a
  root sequence, or the reverse (the rest of the file silently dropped); a leading BOM (read
  into the first key).
- **Gaps (valid YAML refused as if broken):** quoted scalars continued onto the next line (6
  real files); a more-indented `- b` under a plain item `- a` (PyYAML folds to `"a - b"`).
- 77 refusals of already-declared constructs (ambiguous booleans, flow sets); 62 are `on:` in
  `.github/workflows`.

Rulings taken: out-of-subset valid YAML is **YELLOW**; default scope is the **docs dirs plus
globs a project declares**; the **PostToolUse watcher also reports** at write time.

## Design

### 1. Two kinds of refusal — `scripts/riteyaml.py`
- `RiteYamlError` gains `kind` (`"invalid"` | `"unsupported"`) and `construct` (a stable id).
  Two subclasses, `YamlInvalid` and `YamlUnsupported`, so every existing
  `except RiteYamlError` keeps working unchanged.
- **unsupported** (valid YAML, outside the subset): anchors, aliases, tags, merge keys, complex
  keys, ambiguous booleans, flow sets, multi-document streams (`---` after content), a
  more-indented `- ` under a plain sequence item (message: "reads as one string; probably a
  nested list missing its parent key").
- **invalid** (YAML forbids it): unterminated quotes/flows, `expected 'key: value'`, unexpected
  indentation, plus the new rejections: plain scalar containing `: ` or ending in `:`; `*`/`&`
  without a name; `@`/backtick starting a plain scalar; tab in indentation; content left after
  the root structure ends (a residual check in `_Reader.parse()` — the general guard against
  every silent early return, not just the two cases found).
- **Widen:** multi-line single- and double-quoted scalars (line break folds to a space, a blank
  line to `\n`, trailing `\` escapes the break in double quotes). Strip a leading BOM.
- **Out of scope, stated:** silent misreads that don't affect validity (YAML 1.1 octal `0600`,
  date/number-shaped keys as strings, `\u` escapes, three undiagnosed block-literal diffs).
  They stay recorded in the concern; a follow-up, not this change.

### 2. The subset is declared — `spec/project-standard.yaml`
- New CORE top-level section `yaml_subset:` beside `file_format` — `supported:` list, and
  `refused:` list of `{construct, kind, example, why}`. `construct` ids match the parser's.
- Also declared there: `checked_files: {include: ["{docs_dir}/**/*.yaml", "{docs_dir}/**/*.yml"]}`
  expanded over `local.docs_dir` default + alternatives, and the rule's tests
  (`yaml_parses` level integrity → RED; `yaml_within_subset` level populated → YELLOW).
- Fix the stale claim in the same section: `file_format.dependency_note` still says "YAML needs PyYAML".
- `participation.marker_contents.optional_keys` += `yaml_check`.
- `spec/render-standard.py`: one render function for `yaml_subset`; regenerate `PROJECT-STANDARD.md`.
- The spec and the parser must not become two drifting copies: **the test asserts the spec's
  refused ids == the ids the MUST_REFUSE / MUST_REJECT_INVALID cases raise** (see Tests). The
  parser reads nothing from the spec at runtime — it stays a standalone module.

### 3. The check — `scripts/rite-check.py` + `scripts/riterules.py`
- `riterules.project_yaml_files(root, spec, marker) -> list[str]` and
  `riterules.yaml_verdict(root, rel) -> (kind|None, message)` — ONE predicate for checker and
  watcher. File list: `git ls-files --cached --others --exclude-standard -z` filtered by the
  globs when the root is a repo (same subprocess conventions as `git_show`: `encoding="utf-8"`,
  `errors="replace"`, timeout); `Ctx.glob_matches`-style case-exact glob otherwise. Gitignored
  YAML is not checked in a repo, and is checked without one — stated in the spec.
- `.rite.yaml` `yaml_check: {include: [...], exclude: [...]}` extends/narrows the default and is
  **reported, never silent**: one NA line counting what it added and excluded.
- In `check()` after the artifact loop: skip paths already covered by an artifact (no double
  RED); for each remaining file one finding — `yaml_parses` RED for invalid, `yaml_within_subset`
  YELLOW for unsupported, naming construct and line. Not stage-gated: broken YAML is wrong at
  `idea`. No collapsing: each line is a distinct file, unlike the stage-deferred NA wall.
- Non-UTF-8 file: RED `yaml_parses` "not UTF-8". (`Ctx.read` catches only OSError; a
  UnicodeDecodeError would crash — handled in the shared predicate, and noted for artifacts.)
- Coverage denominator includes the two new declared tests.
- Rite dogfoods it: its own `.rite.yaml` declares `yaml_check.include: [spec/*.yaml, .github/gates.yaml]`
  (not the workflow — GitHub's `on:` dialect).

### 4. The watcher — `scripts/rite_watch.py`
- `findings_for()` also asks `riterules.yaml_verdict` when the written path is in
  `project_yaml_files` scope or is a YAML artifact. Silent when valid; always exit 0.
- New DECISIONS entry (append, never edit `d-write-discipline-watcher`): the watcher now reports
  three things, and why this one earned it — both real breaks were in-session edits.

## Order (each step proven RED before trusted GREEN)
1. Tests first in `scripts/test-riteyaml.py`: new `MUST_REJECT_INVALID` (synthetic snippets
   only — the repo is public), reclassify `unterminated flow mapping` out of `MUST_REFUSE`,
   `MUST_SUPPORT` += multi-line quoted, BOM, CRLF. Each case asserts **the oracle agrees with
   the kind**: invalid ⇒ PyYAML raises; unsupported ⇒ PyYAML accepts. Run → fails.
2. Parser taxonomy + fixes (§1). Run → passes; rite's own 10 documents still identical.
3. Spec section + renderer + parity assertion (§2); regenerate; `--check` passes.
4. Checker rule (§3) with fixtures in `scripts/test-checker-verdicts.py`: broken non-artifact
   YAML → one RED naming it; out-of-subset → YELLOW; broken artifact → exactly one RED; declared
   exclude → counted NA; gitignored YAML untouched in a repo; non-git project uses filesystem.
5. Watcher (§4) with a case in `scripts/test-watch-discipline.py`.
6. `test-riteyaml.py` without PyYAML: run the oracle-free half (kinds, parity) and FAIL on it;
   exit 2 only for the oracle half. Update `skip_means`/`skip_short` in `.github/gates.yaml` —
   no new gate, so the generated counts don't move.
7. Docs: DECISIONS (`d-project-yaml-checked-against-declared-subset`, watcher entry); retire
   `c-project-yaml-is-not-checked` as settled; ROADMAP milestone + current_state sentences;
   ARCHITECTURE (riteyaml line count is stale: says 358, is 502; describe the two kinds);
   CLAUDE.md trap bullet on the parser; README honest limit ("validity is judged by a declared
   subset, not by full YAML"); `template/.rite.yaml` commented `yaml_check` example; LOG.
8. `.claude-plugin/plugin.json` 0.22.0 → 0.23.0 (a changed subset is not a patch).

## Verification
- `python3 scripts/test-riteyaml.py`, `scripts/test-checker-verdicts.py`,
  `scripts/test-watch-discipline.py`, `scripts/test-portability-rules.py`, and
  `python3 .github/run-gates.py` — all gates.
- `spec/render-standard.py --check`, `--protocol --check`, `--blocks --check`.
- Re-run the scratchpad corpus measurement: **FALSE_ACCEPT = 0**; every remaining refusal of a
  PyYAML-valid file is a declared `unsupported` construct; the 22 invalid files still rejected.
- Against the adopting project's history: the two broken revisions → RED `yaml_parses`; HEAD → 0 RED.
- `bash hooks/rite.sh check .` on rite → 0 RED except the session-scoped HANDOFF RED until `/rite:end`.
- A throwaway fixture: write a broken `docs/X.yaml` through the watcher entry point → one report line.
- `test-installed-current.py` fails until the plugin is updated to 0.23.0 — that update touches
  `~/.claude/plugins`, so it is run only with Costin's go-ahead.

## Not in this change
- Commit gate (`c-commit-is-not-gated`), source definition (`c-source-is-filesystem-mtime`),
  copier, memory lane, ROADMAP wording — separate concerns, untouched.
- Silent misreads that don't affect validity (§1).
- YAML front matter in non-artifact Markdown.
- Uppercase `.YAML`/`.YML` extensions: not matched by the case-exact globs; declared, not handled.
