---
name: preflight
description: Run the project standard's checks and report the verdict with whose-side-to-fix, plus which capabilities are present. Read-only — reports, never fixes, never installs.
argument-hint: "(none = this project) | <path> = another project | --force = evaluate a project that has not opted in"
---

Run Rite's checker against the project and show what it found. **Read-only surfacing** — it
reports and tags whose side each finding is on; the user decides what to do.

Participation is opt-in: a project without a `.rite.yaml` marker is not checked and nothing is
printed. Use `--force` to answer "what would this project score if it opted in?", which is the
only way to evaluate before adopting.

## Steps

1. Run the checker via Bash:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/rite-check.py" [PATH] [--force]
   ```

   Resolve `PATH` from `$ARGUMENTS`; default to the current project.

2. Show the output **verbatim** in a fenced block. It emits one line per non-green finding,
   tagged with severity and side, then a count and a coverage line. Do not paraphrase, filter
   or re-order it.

3. Append **one** judgment line naming the single most actionable finding and whose side it is
   on. Lead with a RED if there is one, otherwise the highest-impact YELLOW. If everything is
   green, say so in one line.

4. Read the coverage line and say what it means if it matters: a rule declared in the standard
   but not implemented by the checker reports `NA`, deliberately, so the gap between what the
   standard claims and what it can verify stays visible.

5. If asked about capabilities, report what is present — Python, git, PyYAML — and what each
   one enables or costs. Report **three states**, not two: absent, present-but-broken, and
   working. A broken interpreter is not the same problem as a missing one.

## Don't

- **Don't tell the user to install anything, and don't print a command to paste.** You cannot
  see the machine's existing state — system python, pyenv, conda, the Store alias, WSL — so an
  install instruction is a guess with their working environment as the stake. Name what is
  missing and what is unavailable because of it. If they ask how to fix it, link the vendor's
  documentation.
- **Don't modify the environment.** No installs, no PATH edits, no writes to python, pyenv or
  git config. Detection is read-only by construction.
- **Don't probe for `python` by invoking it on Windows** — the App Execution Alias opens the
  Microsoft Store, so the detection would cause the surprise it exists to prevent.
- **Don't auto-fix findings.** Rite surfaces and tags whose-side-to-fix; the user decides.
- Don't paraphrase the checker output — show it as-is, then add the one judgment line.
