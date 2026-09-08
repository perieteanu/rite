#!/usr/bin/env bash
# claude-plugin-probe — install a Claude Code plugin and show exactly what changed.
#
# WHY THIS EXISTS
# Installing a plugin is reversible (`claude plugin disable`), so the risk is not that you
# cannot undo it. The risk is that you do not NOTICE what it did. A plugin can shadow an
# existing slash command silently: you would discover it days later, when /log stopped
# behaving the way it used to, having half-learned a new behaviour.
#
# So this is a PROBE, not an installer. It snapshots state, performs the install, snapshots
# again, and diffs. It reports; it never judges and never fixes. If a collision shows up,
# what to do about it is a decision, not a script's business.
#
# USAGE
#   claude-plugin-probe-20260908.sh <marketplace-path> <plugin-name>   # on  + diff
#   claude-plugin-probe-20260908.sh --off <plugin-name> [<marketplace-name>]  # off + diff back
#   claude-plugin-probe-20260908.sh --snapshot                          # capture only
#
# No sudo. Idempotent: re-running the install path is harmless.
# Candidate to graduate to ~/projects/bin/ if it proves useful more than twice.
set -euo pipefail

STATE="$HOME/projects/claude-run/.plugin-probe"
SETTINGS="$HOME/.claude/settings.json"
mkdir -p "$STATE"

snapshot() {  # $1 = label
  local d="$STATE/$1"
  mkdir -p "$d"
  echo "  → snapshotting state as '$1'"
  cp "$SETTINGS" "$d/settings.json" 2>/dev/null || echo '{}' > "$d/settings.json"
  claude plugin list            > "$d/plugins.txt"      2>&1 || true
  claude plugin marketplace list > "$d/marketplaces.txt" 2>&1 || true
  ls -1 "$HOME/.claude/commands" 2>/dev/null | sed 's/\.md$//' | sort > "$d/commands.txt" || true
}

json_diff() {  # $1 = before file, $2 = after file
  python3 - "$1" "$2" <<'PY'
import json, sys
def load(p):
    try: return json.load(open(p))
    except Exception: return {}
a, b = load(sys.argv[1]), load(sys.argv[2])
def walk(x, y, path=""):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in dict.fromkeys(list(x) + list(y)):
            walk(x.get(k, "<absent>"), y.get(k, "<absent>"), f"{path}.{k}")
    elif x != y:
        sa, sb = json.dumps(x)[:120], json.dumps(y)[:120]
        print(f"  {path}\n      before: {sa}\n      after:  {sb}")
walk(a, b)
PY
}

report() {  # $1 = before label, $2 = after label
  local b="$STATE/$1" a="$STATE/$2"
  echo
  echo "════════ settings.json"
  local out; out="$(json_diff "$b/settings.json" "$a/settings.json")"
  [ -n "$out" ] && echo "$out" || echo "  (unchanged)"
  echo
  echo "════════ marketplaces"
  diff <(grep -oE '^\s+[❯*]?\s*\S+' "$b/marketplaces.txt" || true) \
       <(grep -oE '^\s+[❯*]?\s*\S+' "$a/marketplaces.txt" || true) || true
  echo
  echo "════════ plugins"
  diff "$b/plugins.txt" "$a/plugins.txt" || true
}

collisions() {  # $1 = path to the plugin/marketplace root
  echo
  echo "════════ NAME COLLISIONS (the thing that fails silently)"
  local root="$1" found=0
  while IFS= read -r skill; do
    local name; name="$(basename "$(dirname "$skill")")"
    if [ -f "$HOME/.claude/commands/$name.md" ]; then
      echo "  ⚠ '$name' exists BOTH as your ~/.claude/commands/$name.md"
      echo "     and as a plugin skill. Test which one bare /$name resolves to."
      found=1
    fi
  done < <(find "$root" -path '*/skills/*/SKILL.md' 2>/dev/null)
  [ "$found" -eq 0 ] && echo "  none — no plugin skill shares a name with your commands"
  return 0
}

# ─── modes ───────────────────────────────────────────────────────────────────
if [ "${1:-}" = "--snapshot" ]; then
  echo "== snapshot only, no changes =="
  snapshot "manual-$(date +%H%M%S)"
  echo "done."
  exit 0
fi

if [ "${1:-}" = "--off" ]; then
  plugin="${2:?usage: --off <plugin-name> [<marketplace-name>]}"
  market="${3:-$plugin}"
  echo "== REVERSING: disable '$plugin', remove marketplace '$market' =="
  snapshot after-on
  echo "  → claude plugin disable $plugin"
  claude plugin disable "$plugin" 2>&1 | sed 's/^/     /' || true
  echo "  → claude plugin marketplace remove $market"
  claude plugin marketplace remove "$market" 2>&1 | sed 's/^/     /' || true
  snapshot after-off
  echo
  echo "Diff BEFORE-INSTALL vs AFTER-REVERT — anything listed here did NOT come back:"
  report before after-off
  echo
  echo "If settings.json shows leftovers, the pre-install backup is the ground truth:"
  ls -1t "$HOME"/.claude/settings.json.bak-* 2>/dev/null | head -3 | sed 's/^/  /'
  exit 0
fi

market_path="${1:?usage: <marketplace-path> <plugin-name>}"
plugin="${2:?usage: <marketplace-path> <plugin-name>}"
market_path="$(cd "$market_path" && pwd)"

echo "== PROBE: install '$plugin' from $market_path =="
echo
echo "-- 1. backup + snapshot BEFORE"
cp "$SETTINGS" "$SETTINGS.bak-$(date +%Y%m%dT%H%M%S)"
snapshot before
collisions "$market_path"

echo
echo "-- 2. add the marketplace"
claude plugin marketplace add "$market_path" 2>&1 | sed 's/^/     /'

echo
echo "-- 3. install the plugin"
claude plugin install "$plugin" 2>&1 | sed 's/^/     /'

echo
echo "-- 4. snapshot AFTER"
snapshot after-on

echo
echo "-- 5. what the plugin actually resolved to"
claude plugin details "$plugin" 2>&1 | sed 's/^/     /' || true

report before after-on

echo
echo "════════ WHAT TO CHECK YOURSELF"
echo "  This script does not judge. Two things it cannot test from outside a session:"
echo "    a) type /  and see whether the plugin's commands appear, and under what names"
echo "    b) run a colliding command (if any were listed above) and confirm which one ran"
echo
echo "  To reverse:  $0 --off $plugin"
