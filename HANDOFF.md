---
# WRITE DISCIPLINE — mixed. The text and the keys above session_end are write-once: a change
# means a NEW file. session_end and closed are the close record, rewritten by every close.
genre: state
written: "2026-10-28"
expires: "2027-01-26"
status: live
session_end: written
closed: "2026-10-28"
supersedes: "the 2026-09-19 handoff — its one action, the git-install test, was never run and is carried below; its waiting list is carried too, and the 09-25 harvest session that should have replaced it never closed"
---

# HANDOFF — rite

State is in `ROADMAP.current_state`. This is what the docs do not say.

## Verify first
- **On the next SessionStart in an adopting project, there must be no crash line.** Three
  adopters now carry one YELLOW each (`list_items_have_keys` — milestones dated `date:` with no
  `closed:`). Those are TRUE findings in their own files and migrating them is their opt-in, not
  a Rite regression.

## Still never done: the git-install test
Carried unchanged from 2026-09-19. Run it only right after a close, because removing the
directory marketplace removes `/rite:end` with it:

```
claude plugin uninstall rite@rite
claude plugin marketplace remove rite
claude plugin marketplace add perieteanu/rite
claude plugin install rite@rite
# restart; confirm the SessionStart verdict appears and /rite:preflight runs
claude plugin uninstall rite@rite && claude plugin marketplace remove rite
claude plugin marketplace add ~/projects/rite && claude plugin install rite@rite
```

It now also answers the open half of `c-directory-marketplace-serves-the-working-tree`: whether
hooks, not just skills, run from the tree.

## Waiting on Costin, not on code
- **"Should the public repo be just the plugin?"** Raised at this close: his memory was that
  rite-lab holds plugin plus history and rite only the plugin. In fact rite holds plugin plus the
  reasoning, by his own 09-19 ruling. A plugin-only repository would re-decide
  `d-refound-public-repo-diary-stays-private` and needs the sync that decision refused. Not
  raised as a concern yet; ask.
- **`c-log-has-writers-outside-the-session`** — his words, "the issue is deeper". A dedicated
  session per `d-project-tracker-stays-separate`, never folded into other work.
- **`c-close-record-is-a-date`** — the after-midnight false RED. Small and measured; the best
  next BUILD item.
- Carried from 09-19, still unruled: the Console account for the community marketplace;
  `c-session-post-is-gated-by-participation`; `c-watcher-cannot-see-shell-writes` (a vs b);
  three ids sitting in both `concerns` and `retired_ids`; the two 09-13 entries at the top of
  `retired_ids`.
- `next-steps.yaml` still lists the no_done_markers fix for rite. It is project-tracker's file;
  removal proposed to him at this close.

## Traps this session paid for
- **Every edit in this working tree is live in every adopting project the moment it is saved.**
  The `installed-copy` gate compares the cache, which is not what runs here. Keep WIP short, or
  on a branch.
- **A plan approval can reach the session while Costin never saw it.** His window was blocked;
  the tool said "approved". Confirm after any interface hiccup (memory note in ~/.claude).
- **A known defect is not a cheap defect.** The tracker said fifteen minutes; leaving it open
  for 33 days cost four separate re-diagnoses in adopting sessions.
- **Two of my own claims were wrong and a one-file fixture beat re-reading**: that key_aliases
  weakens the near_term check (the checker reads no alias), and that README and CLAUDE.md said the
  installed copy runs (only ROADMAP did).
- **A count in prose is a claim about the future.** "the two commit counts will never match
  again" — both read 75 today.

## Found, deliberately not fixed
- Still hardcoded, carried: `HANDOFF_LIFETIME_DAYS = 90` (scripts/rite_init.py); the
  `~/.claude/rite` fallback when CLAUDE_PLUGIN_DATA is unset.
- `tests/field-2026-09-19..25/` says of itself "delete once the harvest is done"; the harvest is
  done. Deleting is his.
- The 0.28.0 directory is still in the plugin cache beside 0.29.0. Harmless; removal is his.
- CI: Node.js 20 deprecation on `actions/checkout@v4` and `actions/setup-python@v5`, carried.
