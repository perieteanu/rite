#!/usr/bin/env bash
# Falsification experiments for tests/peugeot307sw findings 1, 2, 3, 6.
set -uo pipefail
R=/home/perieteanu/projects/rite
FX="$R/tests/peugeot307sw/repro/build-fixture.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
fresh() { grep -E 'newest_entry_within_days_of_activity|as_of_within_days_of_activity' | sed 's/^ */    /'; }
commit() { ( cd "$1" && git add -A && git -c user.email=x@x.invalid -c user.name=x commit -q -m "$2" ); }

echo "=== F2a: documents-only fixture + ONLY a .gitignore (no script) ==="
"$FX" "$T/a" spec full >/dev/null
printf 'secrets/\n' > "$T/a/.gitignore"; commit "$T/a" gitignore
bash "$R/hooks/rite.sh" check "$T/a" 2>&1 | fresh

echo "=== F2b: + one gate script, then its mtime backdated to the docs' date (content identical) ==="
"$FX" "$T/b" spec full >/dev/null
mkdir -p "$T/b/tools"; printf '#!/usr/bin/env bash\necho ok\n' > "$T/b/tools/c.sh"; commit "$T/b" tool
echo "  -- mtime now:";        bash "$R/hooks/rite.sh" check "$T/b" 2>&1 | fresh
touch -d 2026-01-01 "$T/b/tools/c.sh"
echo "  -- mtime 2026-01-01:"; bash "$R/hooks/rite.sh" check "$T/b" 2>&1 | fresh

echo "=== F2c: + an UNTRACKED, gitignored reference file (sources/x.pdf), nothing committed ==="
"$FX" "$T/c" spec full >/dev/null
mkdir -p "$T/c/sources"; printf 'pdf' > "$T/c/sources/x.pdf"
printf 'sources/\n' > "$T/c/.git/info/exclude"
( cd "$T/c" && echo "  git status: $(git status --short | wc -l) changes visible to git" )
bash "$R/hooks/rite.sh" check "$T/c" 2>&1 | fresh

echo "=== F3: broken NON-canonical YAML (docs/WORKLIST.yaml), stages idea and spec ==="
for s in idea spec; do
  "$FX" "$T/d$s" "$s" full >/dev/null
  printf 'items:\n  - a: [unclosed\n' > "$T/d$s/docs/WORKLIST.yaml"
  echo "  -- stage $s:"
  bash "$R/hooks/rite.sh" check "$T/d$s" 2>&1 | grep -E '^ +(RED|YELLOW) |checks ·|WORKLIST' | sed 's/^ */    /'
done

echo "=== F1: present-but-not-yet-required CLAUDE.md with a FALSE claim, at stage idea ==="
"$FX" "$T/e" idea >/dev/null
printf '# e\n\n## What this is\n\nx\n\n<!-- rite:claims\npresent:\n  - docs/NOPE.yaml\n-->\n' > "$T/e/CLAUDE.md"
bash "$R/hooks/rite.sh" check "$T/e" 2>&1 | grep -E '^ +(RED|YELLOW) |checks ·|CLAUDE' | sed 's/^ */    /'

echo "=== F6: copy --plans --dry-run on a fresh fixture ==="
"$FX" "$T/g" idea >/dev/null
out="$(bash "$R/hooks/rite.sh" copy --plans --dry-run --project "$T/g" 2>&1)"
echo "  elsewhere lines: $(printf '%s\n' "$out" | grep -c elsewhere)"
echo "  total lines:     $(printf '%s\n' "$out" | wc -l)"
printf '%s\n' "$out" | head -4 | sed 's/^/    /'
