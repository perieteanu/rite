<!-- Copied from ~/.claude/plans/peppy-chasing-boole.md on 2026-09-12.
     Plans are written outside the project under harness-generated names carrying no
     project attribution; they are lost when the session ends unless copied. Canonical
     name per spec/project-standard.yaml artifact `plan_copy`. Copied by rite_copy.py,
     which attributes a plan to the project whose SESSION wrote it. -->

# Legacy docs layout becomes a declaration, and documentation paths stop being literals

## Context

Two problems that turn out to be one.

**The layout.** The standard names `docs/`, and eleven existing projects use `docs-yaml/` with
`.yaml` documents where the standard names Markdown. Rite tolerates that today but nags about it
on every run: hwprivacy scores 27 YELLOW, and **10 of them are the transition** — 6
`canonical_name` (one per file, forever) plus 4 Markdown section rules applied to YAML files,
which no valid YAML can ever satisfy. There is no way to say "this project predates the standard
and will be converted." The `local.docs_dir` block calls itself configurable, but `.rite.yaml`
has no key for it and no script reads one from the marker — the only way to configure it is to
edit Rite's own spec, which for an installed plugin means the installed copy that
`c-installed-spec-is-not-compared` says drifts silently.

**The hardcoding.** Auditing that found the layer underneath. `rite_copy.py` and `rite_init.py`
**read nothing from the spec at all** — every path they write is re-typed from a value the spec
already declares:

| spec declares | code re-types |
|---|---|
| `path: "docs/claude-memory.md"` (:1890) | `DOCS` + `MIRROR_NAME` |
| `path: "docs/session-scripts/<ISO date>/<name>"` (:1796) | `DOCS` + `SCRIPTS_SUBDIR` + its own date format |
| `plan_copy` path | built inline in `copy_plans` |

So the producer of three artifacts and the checker of those same three artifacts hold independent
copies of each path — the failure `riterules.py` was extracted to prevent. Plus `"docs"` re-typed
three times (`riterules.py:142` and `:207` are byte-identical), `("yaml", "md")` twice in
`rite-check.py`, 12 `docs/…` paths across 5 skill prompts, and
`GLOBAL_HOME_SLUG = "-home-perieteanu"` — Costin's username compiled into a published plugin,
where the guard it protects cannot fire on anyone else's machine.

**Outcome.** Old projects declare their layout and get one honest line instead of ten dead ones.
New projects use `docs/` and see no change. No documentation path exists as a literal anywhere,
and a gate fails if one comes back.

## Decisions taken

- **`migrate_by` is optional** (user's call). Present and future → the exception holds. Present
  and past → it lapses and the findings return, naming the missed date. Absent → holds
  indefinitely, and the line says `no migration date set` so the omission is visible.
- **Declaring collapses, never silences** — `overrides_are_never_silent`: *"a narrowed scope that
  nothing states is a silent opt-out… visibility is the control, not a limit."* One counted NA
  line per project, not zero.
- **Format-shaped rules report NA, not YELLOW.** A YAML MISSION cannot satisfy
  `required_sections: [Mission, Constraints, Non-goals]`, so YELLOW is a false accusation. NA
  naming the declared format is the honest verdict — the same principle the source-freshness work
  settled: *a check that cannot know something must never read like one that found nothing wrong.*
- **Deferred, deliberately:** grading YAML documents on substance (a per-format rule set, so
  `MISSION.yaml` is checked for `mission:`/`constraints:`/`non_goals:` keys). No artifact declares
  a `format:` today; the rules are implicit in which tests each artifact lists. That is a separate
  build and it is recorded so a later session does not read it as an oversight.
- **Not in this plan:** `copy --force` (`c-copier-has-no-read-only-preview`) and the watcher's
  shell-write hole (`c-watcher-cannot-see-shell-writes`, still blocked on verifying `FileChanged`).

## The work

### 1. `spec/project-standard.yaml` — one home for every value

- `participation.optional_keys` += `legacy_layout`.
- New `participation.legacy_layout` block declaring `docs_dir`, `formats` (artifact id →
  extension), optional `migrate_by`, the collapse rule, and the lapse behaviour. State plainly
  that it is for projects predating the standard and that `/rite:init` never writes it.
- `local.docs_dir` += `formats: ["md", "yaml"]`, so the extension pair has a declared home.
- Regenerate both readable forms; `--check` and `--protocol --check` must pass.

### 2. `scripts/riterules.py` — the one resolver

Add `docs_dirs(spec, marker)` and `artifact_path(spec, artifact_id, marker)`. Both consult the
spec first and the project's `legacy_layout` second. Replace the two identical
`dirs = [local.get("default") or "docs", …]` blocks at
[riterules.py:142](scripts/riterules.py#L142) and [:207](scripts/riterules.py#L207) with calls.
This is where `riterules` already lives — `git_show`, `zone_of` and `log_future_timestamps` moved
here for exactly this reason.

### 3. `scripts/rite-check.py`

- `_find` ([:166-185](scripts/rite-check.py#L166-L185)) uses `riterules.docs_dirs` and the spec's
  `formats` instead of the literal `("yaml", "md")` at `:176` and `:180`.
- When `legacy_layout` is declared and current: suppress `canonical_name` and the format-shaped
  rules, emit **one** NA line naming the directory, the file count, the deferred rule count and
  the date. Collapse per `d-stage-deferred-checks-are-collapsed`.
- When lapsed: restore every finding and add a YELLOW naming the missed date.

### 4. `scripts/rite_copy.py`

- Delete `DOCS`, `MIRROR_NAME`, `SCRIPTS_SUBDIR`; resolve all three destinations through
  `riterules.artifact_path`. This is the fix for `c-copier-ignores-the-project-it-writes-into`
  and it makes the copier honour a legacy layout for free.
- `GLOBAL_HOME_SLUG = encode_slug(Path.home())` — derived, not configured.

### 5. A resolver command, and the skills stop naming files

New `scripts/rite_paths.py` plus a `paths` action in the tables in
[hooks/rite.sh:27](hooks/rite.sh#L27) and `hooks/rite.ps1`. It prints participation **and** the
resolved document set — which also closes `c-end-ritual-runs-where-its-tools-are-silent`, because
the first thing `/rite:end` shows becomes *"this project has NOT opted in"* where that is true.

Skills consume it through **dynamic context injection** (verified against
[skills.md — Dynamic Context Injection](https://code.claude.com/docs/en/skills.md#dynamic-context-injection)):
the command runs before Claude reads the prompt and its output replaces the placeholder.

```markdown
## Documents for this project
!`bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" paths`
```

Applied to `skills/{end,update,log,handoff,issue}/SKILL.md`. **The canonical `docs/…` names stay
in the step text as the degradation path** — if a user has `disableSkillShellExecution` set the
injected section is simply empty, and the skill behaves exactly as it does today rather than
breaking. Only the prose that *asserts* a path as the project's own is rewritten to defer to the
resolved block.

### 6. The gate — `scripts/test-docs-path-literals.py`

Modelled on `test-portability-rules.py`, which is already the precedent for a normative rule
enforced by a test rather than by memory. Two halves:

- **AST**, over `scripts/*.py`: a string literal matching a documentation-path shape
  (`docs/…`, a bare `"docs"`/`"docs-yaml"`, a canonical artifact filename) outside the declared
  allow-list is a failure.
- **Prose**, over `skills/*.md`: a `docs/<ARTIFACT>` path outside a step-text fallback is a
  failure, since a skill prompt is a command an agent runs.

Register in `.github/gates.yaml` with a `skip_means` if it needs one. **Prove it fails first** —
run it against the current tree and confirm it names all 17 sites before any of them are fixed.
A gate not watched failing is not yet a gate.

### 7. Record it

- `docs/DECISIONS.yaml` — one entry: the legacy layout is a declaration, not a tolerance.
- `docs/CONCERNS.yaml` — retire `c-copier-ignores-the-project-it-writes-into` and
  `c-end-ritual-runs-where-its-tools-are-silent` to `retired_ids` as settled (**moved**, not
  marked settled in place — three entries are currently in both lists, which is the thing to
  avoid repeating). Widen `c-installed-spec-is-not-compared`: the spec now carries per-project
  policy, so a stale installed copy costs more than it did.
- `template/.rite.yaml` — `legacy_layout` as a commented block with a note that it is for
  pre-existing projects only.

## Verification

Evidence, not assertion — each of these is a command with an expected number.

1. **Rite itself unchanged:** `python scripts/rite-check.py --exclude-scope=session` → still
   `0 RED · 0 YELLOW`, coverage still 66 of 66.
2. **The exception works, measured:** `python scripts/rite-check.py ~/projects/hwprivacy --force`
   is **27 YELLOW** today. Copy the tree to a scratch dir, add a `legacy_layout` marker, re-run →
   expect **27 − 10 + 1 = 18 YELLOW**, with one NA naming the declaration. Read-only against the
   real hwprivacy throughout; the marker goes only in the copy.
3. **The lapse works:** same fixture, `migrate_by` set to a past date → the 10 findings return
   plus a YELLOW naming the missed date.
4. **No date works:** omit `migrate_by` → exception holds, line reads `no migration date set`.
5. **New projects unaffected:** `python scripts/test-scaffold.py` → a scaffolded project still
   scores `0 RED, 0 YELLOW, 8 GREEN`, and its `.rite.yaml` carries no `legacy_layout`.
6. **The username fix:** run `rite_copy.py --memory` with `HOME` pointed at a fixture whose slug
   is not `-home-perieteanu`, and assert the "home-root slug is GLOBAL memory" guard fires. It
   cannot today.
7. **The copier writes to the right place:** with a `legacy_layout` fixture declaring `docs-yaml`,
   `rite_copy.py --all -n` names `docs-yaml/…` destinations, not `docs/…`.
8. **The gate catches what it claims:** run it on the tree at `HEAD` before the fix → fails,
   naming all 17 sites. After → passes.
9. **Everything else still holds:** `python .github/run-gates.py`, plus
   `python spec/render-standard.py --check` and `--protocol --check`.

## Risk

The one that matters: **the running checker reads the INSTALLED spec, not this repo's**
(`c-installed-spec-is-not-compared`, and `spec/` is not compared by
`test-installed-current.py`). Every spec change here is invisible to the live plugin until it is
reinstalled, and the gate will not say so. Reinstall and re-run step 1 before believing any
result from a live session.
