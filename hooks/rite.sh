#!/usr/bin/env bash
# rite.sh — launcher shim. Finds a Python interpreter, or explains why it cannot.
#
# This is the ONLY place shell is permitted in Rite (portability.shell_only_as_a_launcher).
# It contains no checks, no parsing and no logic, because it is the one piece of code that
# must be duplicated: the shell is the only executor guaranteed to exist, and .sh and .ps1
# are two implementations. Keeping it to one job is what stops that duplication drifting.
#
# It also closes the one hole Python cannot: the outermost prerequisite cannot report its own
# absence. This runs BEFORE Python exists, so it is the only code that can say Python is
# missing.
#
# Usage:  rite.sh <session-start|session-end|check|copy|watch> [args...]
#         The session actions take hook JSON on stdin. `check` takes [PATH] [--force] and is
#         what the skills call, so that no prompt has to name an interpreter — the rule
#         python_invocation_differs, which two SKILL.md files broke until 2026-09-10.
set -euo pipefail

action="${1:-}"
if [ $# -gt 0 ]; then shift; fi
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# An explicit table, not name-mangling. The checker is scripts/rite-check.py with a HYPHEN
# while the session entry points use underscores, so `${action//-/_}` cannot reach it — and a
# scripts/rite_check.py added beside scripts/rite-check.py to make the mangle work would be a
# trap for every future reader. Five actions, named once, here.
case "$action" in
  session-start) script="$here/../scripts/rite_session_start.py" ;;
  session-end)   script="$here/../scripts/rite_session_end.py" ;;
  check)         script="$here/../scripts/rite-check.py" ;;
  copy)          script="$here/../scripts/rite_copy.py" ;;
  watch)         script="$here/../scripts/rite_watch.py" ;;
  *)             script="" ;;
esac

if [ -z "$script" ] || [ ! -f "$script" ]; then
  echo "rite: no such action '${action}' (session-start, session-end, check, copy, watch)" >&2
  exit 2
fi

for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    exec "$candidate" "$script" "$@"
  fi
done

# Deliberately no install instructions. Rite cannot see whether this machine has a system
# Python, pyenv, conda, the Windows Store alias or WSL, so any command printed here would be
# a guess with the user's working environment as the stake. Name what is missing and what it
# costs; the user decides. See d-never-instruct-installation.
cat >&2 <<'MSG'
rite: no Python 3 interpreter found (tried python3, python, py).

  Unavailable: the session-start verdict, the checker, the memory mirror, plan copying.
  Still working: /rite:end, /rite:log, /rite:handoff — they need no interpreter.

  Rite will not install anything or change your PATH.
MSG
exit 1
