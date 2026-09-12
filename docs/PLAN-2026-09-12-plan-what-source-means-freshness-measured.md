<!-- Copied from ~/.claude/plans/valiant-spinning-sedgewick.md on 2026-09-12.
     Plans are written outside the project under harness-generated names carrying no
     project attribution; they are lost when the session ends unless copied. Canonical
     name per spec/project-standard.yaml artifact `plan_copy`. Copied by rite_copy.py,
     which attributes a plan to the project whose SESSION wrote it. -->

# Plan — What "source" means: freshness measured against recorded change, not file timestamps

## Context

`c-source-is-filesystem-mtime` (high), harvested 2026-09-11 from Rite's first non-code adoption.
`newest_source_mtime()` in [scripts/rite-check.py:232](scripts/rite-check.py#L232) walks
`root.rglob("*")` and takes filesystem mtimes, skipping only `.git`, `docs`, a root-level
`__pycache__`, `.rite.yaml` and four named files. Both freshness rules measure against it —
`newest_entry_within_days_of_activity` (LOG) and `as_of_within_days_of_activity` (ROADMAP,
ARCHITECTURE) — and both report NA "documents-only project" only when it finds nothing at all.

Measured on a documents-only fixture: **each of these alone** turns both rules from NA to YELLOW
with no document changed — a `.gitignore`; one untracked, git-excluded `sources/x.pdf`; one shell
script. **Backdating that script's mtime to the documents' date silences both again.** The verdict
follows the clock on a file, not the content of the tree. CLAUDE.md names this trap by name
("mtime theatre") as the thing that would hollow out the freshness tests; it arrived through the
definition of *source* rather than the definition of `as_of`.

Two consequences beyond the fixture: a fresh clone sets every mtime to clone time, so CI and any
new clone turn YELLOW once a window passes with nothing changed; and a project that improves the
tools policing its own documents makes those documents look stale.

Intended outcome: freshness is measured against **recorded change** — what git says was
committed — with an honest, named NA wherever that cannot be known.

## Measured facts this design rests on

- One `git log` call answers it: `git log -1 --format=%cs -- . ':(exclude)…'` → **2ms**, no
  per-file subprocess fan-out. Verified on rite (`2026-09-12`), peugeot307sw (`2026-09-10`) and
  hwprivacy's legacy `docs-yaml/` (`2026-09-07`).
- Three outcomes are distinguishable, and each needs its own words:
  no commits yet → exit **128**; commits but no non-doc path ever committed → exit 0 with
  **empty** output (documents-only, preserved); otherwise a date.
- A shallow clone reports `rev-parse --is-shallow-repository` = `true` **and still returns a
  date** — which is why it must be refused rather than trusted.
- `plumbing` has **no git and no non-doc file**, so the mtime fallback yields nothing there: the
  documents-only NA survives for exactly the project class `d-noncode-first-class` protects.
- peugeot307sw's `sources/*.pdf`, `secrets/vehicle.env` and `media/` are **gitignored**, so git
  enumeration drops them for free. What remains is `.gitignore`, `.rite.yaml` and `tools/*`.

## Rulings taken (user, 2026-09-12)

- **Dirty working tree:** activity is the newest *commit* date. Uncommitted edits do not count,
  and the finding states that uncommitted source changes exist. A document cannot be stale
  against an edit nothing has recorded yet.
- **Shallow clone:** NA naming the reason. The freshness rules therefore do not run in this
  repo's CI, which is honest rather than convenient.

## Design

### 1. One predicate — `scripts/riterules.py`
`newest_source_date(root, spec, marker) -> SourceActivity` (a `NamedTuple`:
`date`, `reason`, `dirty`, `mode`). Lives beside `git_known_files`/`yaml_verdict` for the same
reason those do: the checker is not the only caller in waiting, and two copies of "what counts as
activity" would be free to disagree.

- **git mode** when `(root / ".git").is_dir()` (same test as `Ctx.is_git`):
  - shallow → `date=None`, reason `shallow clone — commit dates are an artefact of the clone`
  - `git log -1 --format=%cs -- . <excludes>`; exit ≠ 0 → reason `no commits yet`
  - empty stdout → reason `documents-only project — no source has ever been committed`
  - else the date, plus `dirty` from `git status --porcelain -- . <excludes>`
- **mtime mode** otherwise, with the *same declared exclusions*, and `__pycache__` skipped at
  **any** depth (today only a root-level one is skipped). No git, no statement about ignored
  files, so the filesystem is the only available answer — and the finding says `mode=mtime`.
- Subprocess conventions copied from `riterules.git_show`: `encoding="utf-8"`,
  `errors="replace"`, `timeout`. Pathspecs built from POSIX relative paths.

### 2. The definition is declared — `spec/project-standard.yaml`
New CORE section `source_definition:` beside `yaml_subset`, because the current exclusion set is a
hardcoded value with no human-visible home (four directories, four filenames, one `spec/*.md`
special case) and this standard already declares the rest of its vocabulary.

- `excluded_paths:` documentation directories from `local.docs_dir` (default **plus** every
  superseded alternative, as `yaml_subset.checked_files` already does), `README.md`, `CLAUDE.md`,
  `LOG.md`, `HANDOFF.md`, `spec/*.md`, `__pycache__`
- `operational_not_source:` `.rite.yaml` and `.gitignore` — config about how the project is
  handled, never the thing its documents describe. This is the half of the peugeot307sw finding
  that survives git enumeration.
- `enumeration:` git first, mtime fallback, ignored files are not source
- `dirty_tree:` / `shallow:` / `no_commits:` the three rulings and reasons, in the spec's words
- `honest_limits:` a git worktree presents `.git` as a *file*, so it falls back to mtime; and
  `mode=mtime` cannot distinguish a real edit from a fresh checkout — stated, not hidden
- `.rite.yaml` gains `source_exclude:` (a project declaring that its own tooling is not the thing
  its docs describe), reported as a counted line exactly as `yaml_check` is — never silent. Add to
  `participation.marker_contents.optional_keys`.

### 3. The rules report what they measured — `scripts/rite-check.py`
`_as_of_fresh` and `_log_fresh` call the predicate and delete `newest_source_mtime`. Every
message names the basis, so a reader can tell a real verdict from a degraded one:
`as_of 12d behind newest source (window 60d, commit dates)`, plus
`; source has uncommitted changes` when dirty, and the NA reasons verbatim from the predicate.

### 4. Documents that assert the old behaviour
`spec/project-standard.yaml` — ARCHITECTURE's rule still says `means: "Measured against source
mtime, never against another document."`; CLAUDE.md's mtime-theatre trap bullet; the
`partially_resolved`/`corrected` notes in `c-freshness-thresholds-are-guesses`; retire
`c-source-is-filesystem-mtime`; a DECISIONS entry
(`d-source-is-recorded-change-not-file-timestamps`); ROADMAP `current_state` + a `milestones`
entry **appended, not inserted** (`milestones_append_only` caught exactly that mistake yesterday);
`LOG.md`.

### 5. The first test this rule has ever had
`scripts/test-freshness-source.py`, declared as a gate in `.github/gates.yaml` — which moves the
gate count and therefore requires `render-standard.py --blocks` to refill the generated
gate-count and gate-list blocks in README and ARCHITECTURE. The matrix, each case built in a
temp directory:

| case | expected |
|---|---|
| documents-only git repo, `.gitignore` only | NA `documents-only` — the concern's headline |
| gitignored `sources/x.pdf` added | still NA |
| one committed script | a date |
| that script's mtime backdated, content unchanged | **same date** (mtime no longer decides) |
| uncommitted edit to it | same date, `dirty=True` |
| shallow clone | NA `shallow` |
| `git init` with no commit | NA `no commits yet` |
| no git, one script | mtime date, `mode=mtime` |
| `source_exclude: [tools/]` declared | excludes it, and the checker reports the narrowing |

## Verification

- `python3 scripts/test-freshness-source.py`, then `python3 .github/run-gates.py` — all gates,
  including the new one; `--blocks --check` after regenerating.
- Against real projects, read-only: rite (date, git mode), peugeot307sw (`2026-09-10`),
  hwprivacy (`2026-09-07`), plumbing (**NA documents-only** — the case the concern exists for).
- The falsification that started this: rebuild the documents-only fixture from
  `tests/peugeot307sw/repro/build-fixture.sh` and confirm a `.gitignore`, an ignored PDF and a
  backdated script **no longer** move either verdict.
- `bash hooks/rite.sh check .` on rite — expect the `written_not_older_than_newest_log_entry` RED
  until `/rite:end`, and no new RED.
- Plugin version bump + reinstall at the end, since `scripts/` changes (Costin's call, as before).

## Not in this change

- **Calibrating the windows** (60/90/30 days). `c-freshness-thresholds-are-guesses` keeps its
  calibration half; this change fixes what they are measured *against*, which is the defect.
- The other harvested concerns: commit gate, copier, memory lane, ROADMAP vocabulary.
- `c-installed-spec-is-not-compared`, opened today — one line in `COMPARED` plus a test, separate.
- The silent YAML misreads (`c-yaml-values-are-misread-in-ways-that-still-parse`).
