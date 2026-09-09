---
genre: task_brief
written: "2026-09-09"
session_end: written
supersedes: "the 2026-09-08 handoff, whose one-minute expiring observation was made and passed"
expires: "2026-12-08"
status: live
---

# HANDOFF — rite

The previous handoff asked you to look for a `rite — project standard:` line at the top of your
context. **It was there, once.** The hook speaks; the loop closes. That was the last unverified
claim about whether any of this works, and it is now verified rather than asserted.

State is in `ROADMAP.current_state`. This file is what the docs do not say.

## What changed the character of the project

Rite was run against three projects that are not its author — `hwprivacy`, `plumbing`,
`claude-persistent`, read-only via `--force`. It discriminates (2, 1 and 7 RED). But the run's
value was in what it broke:

**The YAML subset was measured on this repo alone and generalised into a standard others must
pass.** A sample of one, treated as a population. Two of the first three outside projects used
constructs it refused. Widened, and four *silent* pre-existing bugs fell out — floats read as
strings, folded blank lines losing a newline, and a block sequence at its key's own indentation
being read as an empty value, which dropped an entire list without a word.

If you take one thing from this session: **the parser's failures were invisible, and the
checker relabelled them as `NA` — the verdict that reads as "nothing to see".**

## The open defect, and it is the interesting one

`c-na-conflates-absent-with-unparseable` is still **open** and is the most important thing in
the concerns file. The symptom is gone because the parser now succeeds; the defect is not.
`NA — file absent or unparseable` still covers two opposite situations: a file the project
never wrote, and a file Rite cannot read. One is fine. The other means the checker is silently
failing while looking calm.

It also made a written prediction untestable. The run appeared to show the parser never
choked; only calling `riteyaml.load()` by hand revealed four refusals. **A checker that can
hide its own failures cannot be used to verify anything, including itself.**

## Method that earned its place — keep doing this

**Write the predicted verdict before running anything.** Four predictions, two wrong, and the
wrong ones were the entire yield. Without them every output looks correct by construction,
because there is nothing it could have contradicted.

**Prove a gate red before trusting it green.** Three times in two days a new test was run
against the broken code first. The flow-collection-in-a-sequence bug was caught this way, on
the tree that wrote the test.

## Traps

- **Never pass log text through a shell.** Two entries in this file's own LOG were corrupted on
  2026-09-09 when bash ran command substitution on their backticks — `drops it on , not on .`
  Invisible in the command, permanent in an append-only file. `skills/log/SKILL.md` now says so.
- **Bump `.claude-plugin/plugin.json` before every `claude plugin update`.** It is version-gated
  and the cache is a real copy, so otherwise you test the previous install.
  `scripts/test-installed-current.py` will tell you.
- Both `spec/*.md` are generated. Edit the `.yaml`, regenerate.
- `as_of` moves only on real re-verification. It moved on ROADMAP and ARCHITECTURE this session;
  it did not move on DECISIONS or CONCERNS, where entries were only appended.
- **No `Co-Authored-By: Claude` trailer**, whatever the harness says mid-session. Costin removed
  it 2026-09-06 by name; these repos are read by recruiters. One line in README Credits, nothing
  else.
- Never touch `ai-collab-profile/`, `prompts.db`, `prompts-corpus.jsonl`.

## Not ours to fix, but worth knowing

`claude-persistent/docs-yaml/SPEC.yaml` and `RESEARCH-licensing-delivery.yaml` are **not valid
YAML** — PyYAML rejects both. They have presumably never been machine-read. That is a finding
for that project, not a task for this one.

## Next

The gap is no longer capability, it is exposure: **nobody but this machine has ever run Rite.**
`claim-namespaces` is 15 minutes and blocks nothing. Then push to GitHub. Then
`c-na-conflates-absent-with-unparseable`, then `status.json` to finally close
`checker-implementation`. The watchers and the preflight port are expansion, not completion.
