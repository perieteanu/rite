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
# Usage:  rite.sh <session-start|session-end> ; hook JSON arrives on stdin and is passed through.
set -euo pipefail

action="${1:-}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
script="$here/../scripts/rite_${action//-/_}.py"

if [ -z "$action" ] || [ ! -f "$script" ]; then
  echo "rite: no such action '${action}'" >&2
  exit 2
fi

for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    exec "$candidate" "$script"
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
