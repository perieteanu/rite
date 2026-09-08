#!/usr/bin/env python3
"""Differential test: riteyaml must parse this project's YAML identically to PyYAML.

This test IS the correctness claim for scripts/riteyaml.py. PyYAML is the ORACLE here, never
a runtime dependency — it is used to prove the replacement and then not shipped.

Per d-stdlib-only-yaml-subset: if this cannot be made to pass, the correct response is to
revert to PyYAML, not to weaken the test.

Run:  python3 scripts/test-riteyaml.py
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import riteyaml  # noqa: E402

try:
    import yaml  # the oracle
except ImportError:
    print("SKIP  PyYAML is not installed — it is the oracle for this test, not a dependency.")
    print("      Install it to verify riteyaml: pip install pyyaml")
    sys.exit(2)


# Every YAML file this project actually carries, plus the front matter of its Markdown.
YAML_FILES = [
    "spec/project-standard.yaml",
    "spec/session-protocol.yaml",
    "docs/DECISIONS.yaml",
    "docs/ROADMAP.yaml",
    "docs/CONCERNS.yaml",
    ".rite.yaml",
]
FRONTMATTER_FILES = [
    "docs/MISSION.md",
    "docs/ARCHITECTURE.md",
    "docs/CONVENTIONS.md",
    "HANDOFF.md",
]

# Constructs the parser must REFUSE, not guess at. Each must raise RiteYamlError.
MUST_REFUSE = {
    "anchor": "base: &defaults\n  a: 1\n",
    "alias": "a: 1\nb: *defaults\n",
    "tag": "when: !!timestamp 2026-09-08\n",
    "block literal": "text: |\n  a literal block\n",
    "merge key": "a:\n  <<: *base\n  b: 2\n",
    "complex key": "? [a, b]\n: value\n",
    "flow mapping": "a: {b: 1}\n",
    "chomping indicator": "text: >-\n  folded, stripped\n",
    "ambiguous boolean": "enabled: yes\n",
}


def differences(a, b, path="$"):
    """Yield human-readable differences between two parsed structures."""
    if type(a) is not type(b):
        yield f"{path}: type {type(a).__name__} vs {type(b).__name__}"
        return
    if isinstance(a, dict):
        for k in dict.fromkeys(list(a) + list(b)):
            if k not in a:
                yield f"{path}.{k}: missing in riteyaml"
            elif k not in b:
                yield f"{path}.{k}: extra in riteyaml"
            else:
                yield from differences(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            yield f"{path}: length {len(b)} vs {len(a)}"
        for n, (x, y) in enumerate(zip(a, b)):
            yield from differences(x, y, f"{path}[{n}]")
    elif a != b:
        yield f"{path}: {b!r} != {a!r}"


def frontmatter(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else None


def main() -> int:
    failures: list[str] = []
    checked = 0

    for rel in YAML_FILES:
        p = ROOT / rel
        if not p.exists():
            failures.append(f"{rel}: MISSING")
            continue
        text = p.read_text(encoding="utf-8")
        expected = yaml.safe_load(text)
        try:
            got = riteyaml.load(text, rel)
        except riteyaml.RiteYamlError as e:
            failures.append(f"{rel}: refused a construct it should support -> {e}")
            continue
        diffs = list(differences(expected, got))
        checked += 1
        if diffs:
            failures.append(f"{rel}: {len(diffs)} difference(s)")
            failures.extend("    " + d for d in diffs[:8])

    for rel in FRONTMATTER_FILES:
        p = ROOT / rel
        if not p.exists():
            continue
        fm = frontmatter(p.read_text(encoding="utf-8"))
        if fm is None:
            failures.append(f"{rel}: no front matter found")
            continue
        expected = yaml.safe_load(fm)
        try:
            got = riteyaml.load(fm, rel + " (front matter)")
        except riteyaml.RiteYamlError as e:
            failures.append(f"{rel} front matter: refused -> {e}")
            continue
        diffs = list(differences(expected, got))
        checked += 1
        if diffs:
            failures.append(f"{rel} front matter: {len(diffs)} difference(s)")
            failures.extend("    " + d for d in diffs[:8])

    # The refusal half. A parser that silently accepts what it cannot represent is the
    # failure mode this whole design exists to avoid, so not-refusing is a test failure.
    refused = 0
    for name, snippet in MUST_REFUSE.items():
        try:
            riteyaml.load(snippet, f"<{name}>")
        except riteyaml.RiteYamlError:
            refused += 1
        else:
            failures.append(f"did NOT refuse {name} — it guessed instead")

    if failures:
        print(f"FAIL  {len(failures)} problem(s)\n")
        for f in failures:
            print(" ", f)
        return 1

    print(f"PASS  {checked} document(s) parsed identically to PyYAML; "
          f"{refused}/{len(MUST_REFUSE)} out-of-subset constructs refused")
    return 0


if __name__ == "__main__":
    sys.exit(main())
