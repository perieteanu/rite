---
# WRITE DISCIPLINE — mixed. The text and the keys above session_end are write-once: a change
# means a NEW file. session_end and closed are the close record, rewritten by every close.
genre: state
written: "2026-09-19"
expires: "2026-12-19"
status: live
session_end: written
closed: "2026-09-19"
supersedes: "the 2026-09-16 handoff — its verify-first item (haircut's carried_forward close) is now moot: haircut installs from the marketplace this session rebuilt, and the repository it pointed at no longer exists under that name"
---

# HANDOFF — rite

State is in `ROADMAP.current_state`. This is what the docs do not say.

## Verify first
**Nothing. Do the git-install test before anything else.** It is the only outstanding action and
it was deliberately sequenced after this close, because the two marketplaces collide on the name
`rite`: removing the directory source removes `/rite:end` with it. Sequence, then revert —
a git source would make `test-installed-current.py` compare the cache against pushed commits and
go RED on every uncommitted edit, which is a gate switched off within a week.

```
claude plugin uninstall rite@rite
claude plugin marketplace remove rite
claude plugin marketplace add perieteanu/rite
claude plugin install rite@rite
# restart; confirm the SessionStart verdict appears and /rite:preflight runs
claude plugin uninstall rite@rite && claude plugin marketplace remove rite
claude plugin marketplace add ~/projects/rite && claude plugin install rite@rite
```

What it proves: the clone, manifest resolution and hook registration over git, which no session
has ever exercised. What it does NOT prove: a cold machine. This one has the working tree at the
same path, a populated `${CLAUDE_PLUGIN_DATA}`, and credentials that resolve the repo without
thinking. That gap closes only when someone else runs Rite.

## The shape of the world changed today, and two habits are now wrong
- **There are two repositories.** Public `perieteanu/rite` (the tool and the argument, 70
  commits) and private `perieteanu/rite-lab` (the full archive, 75 commits, frozen — nothing
  pushes to it, ever). `~/projects/rite-lab` is its working tree and should stay untouched.
- **Three artifacts are untracked on purpose** — the memory mirror, plan copies, session
  scripts. They are written, they live on disk, the checker grades them, and they are never
  pushed. Re-adding them is the mistake, not the fix.
- **`LOG.md` is public again.** Entries carry timestamps to GitHub. Redaction is by discipline
  alone, by Costin's ruling — `c-log-redaction-has-no-completion-test` holds the reasoning, the
  measured base rate and the declined watcher design. Do not re-propose it unless something leaks.

## Waiting on Costin, not on code
- **A Console account** at platform.claude.com. Everything else for a community-marketplace
  submission is done and measured; the roadmap item carries the requirements. Note the timing
  constraint recorded there: approved plugins are pinned to a commit SHA, so any history rewrite
  must happen BEFORE submitting.
- `c-session-post-is-gated-by-participation` — still a ruling, untouched for days.
- `c-watcher-cannot-see-shell-writes` — the (a) per-session hash snapshot vs (b) stateless mtime
  choice, carried from the 2026-09-16 handoff and still open. Claude leans (a). Write the failing
  Bash-append test before the watcher. **This is the next BUILD item** once the install test is done.
- Three concerns sit in both `concerns` and `retired_ids` (c-source-is-filesystem-mtime,
  c-project-yaml-is-not-checked, c-readme-sample-output-is-a-copy). Still unruled.
- `retired_ids` is append-only, but the two 2026-09-13 entries sit at its top. Moving them is
  itself a reorder. Still unruled.

## Traps this session paid for
- **A rule written to protect can be too wide, and its author trips it first.** The redaction
  convention banned the words `~/.ssh` and `id_ed25519`; two entries written minutes later matched
  while disclosing nothing. Refined to instance rather than class. A rule that makes a real
  finding unrecordable gets ignored entirely rather than narrowly.
- **The checker catches your own migration.** `claims_match_filesystem` went RED on the filtered
  clone because ROADMAP claimed `docs/session-scripts` present — true on this machine, false for
  every clone. "Present for me" is not a claim.
- **`claude plugin validate .` at this root validates ONLY `marketplace.json`.** Name the manifest:
  `claude plugin validate .claude-plugin/plugin.json`. It passes with one warning about the root
  CLAUDE.md, which is correct to ignore — the validator cannot see that this directory is also a
  project.
- **`update` is safer than reinstall.** `claude plugin update` left `settings.json` byte-identical;
  the rewrite the install probe caught belongs to `install`.
- **An aggregate is not a finding.** "85 unique cloners" was ~120 CI clones from a 3-OS matrix,
  each ephemeral runner counted as a unique. Subtract your own activity before raising an alarm.

## Built but never exercised
- `carried_forward` has still never been recorded in a real close.
- `rite.ps1 init` — no PowerShell here, CI does not run the shims.
- `legacy_layout` — still no real user.
- The seeded `.gitignore` has never reached a project other than a temp directory.

## Found, deliberately not fixed
- Hardcoded: `HANDOFF_LIFETIME_DAYS = 90` (scripts/rite_init.py); the `~/.claude/rite` fallback
  when CLAUDE_PLUGIN_DATA is unset (rite_watch.py, rite_preflight.py), which writes into ~/.claude.
- CI: Node.js 20 deprecation on `actions/checkout@v4`, `actions/setup-python@v5`.
- The harness instructed shell-based file edits mid-session, against CLAUDE.md and two standing
  memories. Named out loud and refused. Expect it again.
