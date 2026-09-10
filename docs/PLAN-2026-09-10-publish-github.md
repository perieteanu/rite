# Publish Rite — with the two defects found on the way out

## Context

`ROADMAP.near_term` holds one item, `publish-github`, and the handoff says nothing technical is
in the way. Verifying that claim rather than accepting it turned up three things:

1. **The pre-publish check is already answered, and CLAUDE.md is wrong about it.** Running the
   checker against a `stage: shipped` copy shows LICENSE GREEN — and it is GREEN at `build` too.
   `required_from_stage` gates whether an artifact is *demanded*, not whether it is *checked when
   present*. `CLAUDE.md:94` claims the check "is NA until the commit that publishes". False.
2. **`python_invocation_differs` is a declared rule that nothing enforces**, and two shipped skill
   prompts violate it. `grep -rn python_invocation_differs --include='*.py'` returns one hit: the
   spec declaring it. Meanwhile `skills/preflight/SKILL.md:19` and `skills/end/SKILL.md:55`
   hardcode `python3` — the exact failure the Windows CI run proved is real on 2026-09-10.
3. **`hooks/rite.ps1` is unreachable in production.** `hooks/hooks.json` invokes
   `bash rite.sh` for all three events and never references the `.ps1`. CI exercised it directly,
   so it passed. Windows without Git Bash has no working hook today. **Out of scope here** —
   recorded as a concern, not fixed in this change.

Intended outcome: the two live defects fixed, the stage-table duplication closed with a mechanism
rather than a promise, then the repository published.

`--help` / unknown-flag rejection in `rite-check.py` is deferred to after publishing, by decision.

---

## Step 1 — Commit the mirror bump

`docs/claude-memory.md` is a one-line sync-timestamp change written by the
`claude-mirror-memory` PostToolUse hook. Commit alone; clears the preflight YELLOW.

## Step 2 — The shim gains a `check` action, and the skills stop hardcoding `python3`

`hooks/rite.sh` maps `<action>` → `scripts/rite_<action>.py` and passes no arguments. Two changes,
made **identically in `rite.sh` and `rite.ps1`** — they are deliberate duplicates
(`portability.shell_only_as_a_launcher`) and drift between them is the risk:

- **Action table instead of name-mangling.** `session-start` → `rite_session_start.py`,
  `session-end` → `rite_session_end.py`, `check` → `rite-check.py`. The hyphen/underscore split is
  why a bare mangle will not do, and a `scripts/rite_check.py` sitting beside
  `scripts/rite-check.py` would be a trap.
- **Argument passthrough** (`"$@"` / `@args`) so `check` can take `[PATH] [--force]`.
  Session actions receive nothing extra and keep taking hook JSON on stdin.

Then rewrite the two call sites to go through the shim, naming both forms honestly:

- `skills/preflight/SKILL.md:19`
- `skills/end/SKILL.md:55`

Give the rule a completion test — it is currently declared and unenforced, which is the thing this
project exists to attack:

- **Extend `scripts/test-portability-rules.py`** with a `python_invocation_differs` check. It
  already parses the tree for the stdio rule; this adds a scan of `skills/**/SKILL.md`,
  `hooks/hooks.json` and the rewrite-only docs for a hardcoded `python3` outside the shim.
- `hooks/rite.sh`, `hooks/rite.ps1` and `spec/project-standard.yaml:391` are the legitimate
  mentions — the shim *is* the place that names all three interpreters, and the spec states the
  rule. Exempt those three paths explicitly.

**Known violations this will surface**, to be fixed in the same step: `docs/CONVENTIONS.md:216`
and `spec/PROJECT-STANDARD.md:165` (fix in `spec/project-standard.yaml`, then re-render — the
`.md` is generated), and `ROADMAP.if_revisiting_cold`. `LOG.md`, `docs/DECISIONS.yaml` and
`docs/PLAN-*.md` are append-only or write-once and are **not** touched.

## Step 3 — The stage table gets one home and a guard

**3a. A block-generation mode in the renderer.** `spec/render-standard.py` is whole-file only
today (`SPEC`/`OUT` globals, swapped by `--protocol`). Add a third mode, `--blocks` and
`--blocks --check`, which finds marker pairs in declared files and fills or compares them:

```
<!-- rite:generated stage-table -->   ...   <!-- /rite:generated -->    (Markdown)
# rite:generated stage-table          ...   # /rite:generated           (YAML comments)
```

Targets are **declared in `spec/project-standard.yaml`** under a new `generated_blocks:` key, not
hardcoded in the renderer — the spec is already the authority for what is generated, and a path
list living only in code is a hardcoded value with no human-visible home.

Two targets: `README.md:90-95` (the Markdown table) and `template/.rite.yaml:11-14` (the aligned
comment block). Both currently match the spec, so this change should be a no-op in content — if
it is not, the diff is a bug found.

**3b. `CLAUDE.md` loses its copy rather than generating one.** `CLAUDE.md:95-101` states the
mapping as a prose sentence mid-bullet. Delete the four-item enumeration; keep the rule ("stage
gates the standard, not tier", "a declaration beats tier", "deleting `stage:` does not make the
standard lenient") and point at the spec. Fewest copies wins, and no new machinery is needed for
one bullet. **Fix `CLAUDE.md:94` in the same edit** — the false LICENSE-NA claim from Context (1).

**3c. A guard so a fourth copy cannot appear.** A new gate script that fails when a stage
enumeration appears outside a `rite:generated` block. It reads an **allowlist of the live,
rewrite-only documents a reader acts on**: `README.md`, `CLAUDE.md`, `template/.rite.yaml`,
`docs/*.md`. It does **not** read `LOG.md`, `docs/DECISIONS.yaml` or `docs/CONCERNS.yaml` — those
are append-only records of what was true then, and the project already rules that a milestone
entry saying "seven gates" stays as written. A repo-wide grep with an exclusion list was rejected:
the exclusion list is itself an unchecked hand-maintained copy.

**3d. Register both new gates in `.github/gates.yaml`** — the one home for the gate list, read by
`.github/run-gates.py` via `riteyaml`. The gate count moves 9 → 11, which will falsify every
sentence stating it. Grep for the number and fix the rewrite-only ones only.

**3e. Retire `c-stage-table-duplicated-in-three-places`** in `docs/CONCERNS.yaml` as `settled`,
and append the DECISIONS entry it points to.

## Step 4 — Publish

Not started until Steps 1-3 are committed and all gates pass. The commit does three things at
once, per `ROADMAP.near_term.publish-github.checklist`:

1. `stage: build` → `stage: shipped` in `.rite.yaml`, replacing the comment block that explains
   why it says `build`.
2. Rewrite the README **Status** paragraph (`README.md:11-13`) — "Not published yet — the
   repository is private" and "Treat the install instructions below as what will work, not as what
   you can do today" both become false in this commit.
3. Rewrite `ROADMAP.current_state` and close `publish-github`: **delete** it from `near_term` and
   **append** a `milestones` entry naming its id. `near_term` then stands empty.

Then, and only then, `gh repo edit --visibility public`. That is the irreversible half: `main` is
published in full, `LOG.md` included, per `d-publish-main-in-full-no-export`.

Also: bump `.claude-plugin/plugin.json` from `0.8.1` before any `claude plugin update` — the
installed-copy gate is version-gated and caught this twice on 2026-09-10.

## Step 5 — Record

`/rite:log` for the session (reads the clock per entry), then `/rite:end` for the handoff.
Append a `c-rite-ps1-unreachable-in-production` concern for Context (3).

---

## Verification

Run at each step, not only at the end:

```
python3 .github/run-gates.py                     # all gates, including the two new ones
python3 spec/render-standard.py --check
python3 spec/render-standard.py --protocol --check
python3 spec/render-standard.py --blocks --check # new
python3 scripts/rite-check.py                    # expect 0 RED
```

Specific expectations, each a claim that can fail:

- **Step 2:** `scripts/test-portability-rules.py` fails *before* the skill edits and passes after.
  If it passes before, the new check is not looking where the violation is.
- **Step 3a:** `--blocks` (write mode) produces **no diff** on first run. Both copies match the
  spec today; a diff means the generator disagrees with what a human wrote, and that is worth
  reading before accepting.
- **Step 3c:** the guard fails when a stage enumeration is temporarily pasted into `README.md`
  outside a block, and passes with it removed. A guard that has never failed has not been tested.
- **Step 4:** `scripts/rite-check.py` after the stage flip — LICENSE must be **GREEN, not RED**,
  and the total must stay 61 checks. Already confirmed on a throwaway copy; re-confirm on the real
  tree because the copy had no `.git`.
- **Step 4, after `gh repo edit`:** `gh repo view --json visibility` reports `PUBLIC`, and CI goes
  green on the public repo with unmetered Actions minutes.

## Not doing

- `--help` / unknown-flag rejection in `rite-check.py` — deferred to after publishing, by decision.
- Fixing `hooks/rite.ps1` being unreachable from `hooks.json` — recorded as a concern only.
- Backfilling `python3` out of `LOG.md`, `docs/DECISIONS.yaml`, `docs/PLAN-*.md` — append-only and
  write-once.
- Moving any `as_of` that is not genuinely re-verified against the thing it describes.
- Migrating the 11 existing projects, or anything else in `deferred_deliberately`.
