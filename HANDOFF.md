---
genre: task_brief
written: "2026-09-13"
session_end: written
supersedes: "the 2026-09-12 evening close, whose verify-first item was answered by the haircut adoption — the load-time injection ran there, and aborted"
expires: "2026-12-12"
status: live
---

# HANDOFF — rite

State is in `ROADMAP.current_state`. This is what the docs do not say.

## The one thing to verify first

**Test the fix from the INSTALLED plugin, in a project other than rite.** Inside this repo the
skills are served from the working tree (`Base directory: projects/rite/skills/end`) even while
`installed_plugins.json` says 0.25.0, so a successful `/rite:end` here proves nothing about what
users get. Run `claude plugin update rite` (0.25.0 → 0.26.0), restart, then `/rite:end` in
`~/projects/haircut`. Three possible outcomes:
- loads, no permission prompt for the resolver step → the allowed-tools pattern matched. Done.
- loads, but prompts → the quoted pattern `Bash(bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" *)`
  did not match after substitution. Harmless, but try an unquoted form and record which works.
- aborts → the diagnosis in `d-session-skills-never-inject-at-load` is incomplete. Stop and read
  the exact error before changing anything.

The `installed-copy` gate stays red until the update; that is expected, not a regression.

## Built but never exercised
- `rite.ps1 init` — added, never run; no PowerShell on this machine and CI does not run shims.
- `legacy_layout` still has no real user. hwprivacy still has no `.rite.yaml` (checked 2026-09-13).

## Open, and what each is waiting on (all verified still `status: open`)
- `c-watcher-cannot-see-shell-writes` (high) — blocked on one lookup: does `FileChanged` fire for
  writes made by a Bash call? Read the hooks reference before designing.
- `c-session-post-is-gated-by-participation` — needs a ruling, not code.
- `c-copier-has-no-read-only-preview` — on a writer, the flag can only mean preview.

## Found, deliberately not fixed
- `docs/CONVENTIONS.md` says the shim prints "how to install it"; `rite.sh` deliberately does not
  (`d-never-instruct-installation`). Its "Missing PyYAML degrades loudly" bullet predates stdlib-only.
- CI annotates `actions/checkout@v4` and `actions/setup-python@v5` as Node.js 20, deprecated.
- Three concerns still sit in BOTH `concerns` and `retired_ids` — `c-source-is-filesystem-mtime`,
  `c-project-yaml-is-not-checked`, `c-readme-sample-output-is-a-copy`. Still unruled.
- `tests/haircut/`, `tests/hwprivacy/` are harvested and can go (gitignored). haircut's repro 01
  now prints an empty-name exit 127 at step 2 — a bug in the repro, not in Rite.

## Traps this session paid for
- **A gate can install the defect it was written to prevent.** half B of the literals gate demanded
  the injection. When a gate requires a harness MECHANISM, check the vendor docs for how that
  mechanism fails, not only that it exists.
- **A rule that bans one name is a preference for the other.** The interpreter rule certified the
  command that broke adoption.
- **The widened gate caught its author** — prose quoting the banned command trips it. Rephrase
  ("a bare-`python` command"); do not add an exemption.

## Do not re-litigate
The resolver is a STEP, never a load-time injection; the interpreter rule covers every name,
with `<python>` as the developer placeholder. Reasoning in `DECISIONS.yaml`, evidence in `LOG.md`.
