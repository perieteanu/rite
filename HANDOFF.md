---
# WRITE DISCIPLINE — mixed. The text and the keys above session_end are write-once: a change
# means a NEW file. session_end and closed are the close record, rewritten by every close.
genre: state
written: "2026-09-16"
expires: "2026-12-16"
status: live
session_end: written
closed: "2026-09-16"
supersedes: "the 2026-09-13 handoff — its verify-first item was answered by haircut's 16-09 /rite:end, which loaded"
---

# HANDOFF — rite

State is in `ROADMAP.current_state`. This is what the docs do not say.

## Verify first
**haircut's close on 0.27.0.** Its 16-09 /rite:end is unrecorded: it stopped at step 4 on the
flaw fixed today. In a session there, the close should change ONLY `session_end:
carried_forward` and add `closed: "<today>"`, plus two LOG lines (the stage-idea decision,
logged late, and the close note). Expected: `closed_not_older_than_newest_log_entry` GREEN,
`written:` still 2026-09-13. If it goes RED, read the finding's wording first — "no close
record" means `closed:` was not written, "last closed" means it was written with an old date.
Its earlier plan to move `written:` is the failure the fix removes; do not accept it.

## Next build, waiting on one ruling
`c-watcher-cannot-see-shell-writes` (high). The hooks lookup is done and recorded in the
concern: FileChanged sees every writer but cannot reach Claude; PostToolBatch can. The open
ruling is (a) per-session hash snapshot vs (b) stateless mtime — Claude leans (a). Write the
failing Bash-append test before the watcher.

## Traps this session paid for
- **Every project on this machine runs the WORKING TREE**, not the install cache — the
  marketplace source is `directory` (c-directory-marketplace-serves-the-working-tree). The
  installed-copy gate compares the cache, so green there does not prove what runs. Only a
  git-sourced install elsewhere tests what a user gets.
- **A chained Bash call defeats the skills' allowed-tools rule.** `rite.sh paths; git status`
  prompts for the second half. The two prompts at haircut's close came from that, so whether
  the quoted pattern matches on its own is still unverified.
- **A probe LOG line needs the machine clock too.** A hand-typed 20:30 at 19:51 went RED on
  no_future_timestamps in a scratch copy.
- **retired_ids is append-only, but the two 2026-09-13 entries sit at its top.** Today's was
  appended at the end. Unruled whether to move them; moving them is itself a reorder.

## Built but never exercised
- `carried_forward` has never been recorded in a real close — haircut is the first.
- `rite.ps1 init` — no PowerShell here, CI does not run the shims.
- `legacy_layout` — still no real user.

## Waiting on Costin, not on code
- `c-session-post-is-gated-by-participation` — a ruling.
- Three concerns sit in both `concerns` and `retired_ids` (c-source-is-filesystem-mtime,
  c-project-yaml-is-not-checked, c-readme-sample-output-is-a-copy).
- `tests/haircut/`, `tests/hwprivacy/` can be deleted (gitignored).
- The founding plan is 8 of 10 done; `vscode-viewer` and `official-marketplace` both wait on
  someone other than Costin running Rite.

## Found, deliberately not fixed
- CI: Node.js 20 deprecation on `actions/checkout@v4`, `actions/setup-python@v5`.
- Hardcoded: `HANDOFF_LIFETIME_DAYS = 90` (scripts/rite_init.py); the `~/.claude/rite`
  fallback when CLAUDE_PLUGIN_DATA is unset (rite_watch.py, rite_preflight.py), which writes
  into ~/.claude.
- `~/.claude/CLAUDE.md` names extension 2.1.263; 2.1.273 is active. Not this repo's file.

## Do not re-litigate
`closed:` is its own key; the rule is `closed_not_older_than_newest_log_entry`; no `closed:`
falls back to `written:`, the stricter reading. Reasoning in
`d-handoff-close-record-is-its-own-field`.
