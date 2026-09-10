#!/usr/bin/env python3
"""Contract test: the INSTALLED copy of Rite must match this working tree.

Closes c-installed-copy-can-be-stale. On 2026-09-08 a correct fix appeared not to work for
several minutes: the source was right, the install cache still held the bug, and
`claude plugin update` answered "already at the latest version" without complaint. The cache
is a real copy, not a symlink, and update is version-gated — so what runs is the last
INSTALLED version, never the working tree.

Documenting that as a release step would have been the wrong fix. "Remember to bump the
version" is a rule with no completion test, which is the thing this project exists to replace.
So it is a check that fails instead.

It lives here rather than in rite-check.py deliberately: rite-check's subject is a PROJECT's
conformance to the standard, and no other consumer of the standard ships a plugin. This is
about Rite's own delivery, so it is a test, not a rule.

Run:  python3 scripts/test-installed-current.py
Exit: 0 pass · 1 fail · 2 skip (Rite is not installed on this machine — not a dependency)
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

# The executable surface. Documents are excluded on purpose: the cache carrying a stale LOG.md
# is untidy, not broken, and failing on it would train people to ignore this test.
COMPARED = ["scripts", "skills", "hooks", ".claude-plugin"]
CACHE = pathlib.Path.home() / ".claude" / "plugins" / "cache"

manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
name, repo_version = manifest["name"], manifest["version"]

installs = sorted(CACHE.glob(f"*/{name}/*")) if CACHE.is_dir() else []
installs = [d for d in installs if d.is_dir()]
if not installs:
    print(f"SKIP  {name} is not installed on this machine — the installed copy is not a "
          f"dependency of the repo.")
    sys.exit(2)

failures: list[str] = []

# 1. Version. A bump is what makes `claude plugin update` do anything at all.
versions = sorted(d.name for d in installs)
if repo_version not in versions:
    failures.append(f"repo is version {repo_version}; installed: {', '.join(versions)}. "
                    f"Bump .claude-plugin/plugin.json and run `claude plugin update {name}`.")

# 2. Content. An equal version with unequal bytes is the worse failure — it looks current.
for d in installs:
    if d.name != repo_version:
        continue
    for rel in COMPARED:
        src = ROOT / rel
        if not src.is_dir():
            continue
        for f in sorted(src.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            mirror = d / f.relative_to(ROOT)
            if not mirror.is_file():
                failures.append(f"missing from the install: {f.relative_to(ROOT)}")
                continue
            # Normalize line endings before any byte comparison (portability rule).
            a = f.read_text(encoding="utf-8").replace("\r\n", "\n")
            b = mirror.read_text(encoding="utf-8").replace("\r\n", "\n")
            if a != b:
                failures.append(f"differs from the install: {f.relative_to(ROOT)}")

if failures:
    print(f"FAIL  the running copy is not this working tree ({len(failures)} finding(s)):")
    for f in failures:
        print(f"        {f}")
    sys.exit(1)
print(f"PASS  installed {name} {repo_version} matches the working tree.")
sys.exit(0)
