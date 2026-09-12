#!/usr/bin/env python3
"""Find values baked into code that arguably belong in spec/project-standard.yaml or .rite.yaml.

Costin's rule: constants and variable defaults in code are wrong; values declared in a
human-visible config file are fine. So the question for every literal is "is this value also
declared in the spec, or is the code the only place it exists?"
"""
import ast
import pathlib
import re
import sys

ROOT = pathlib.Path("/home/perieteanu/projects/rite")
SPEC = (ROOT / "spec" / "project-standard.yaml").read_text(encoding="utf-8")
PROTO = (ROOT / "spec" / "session-protocol.yaml").read_text(encoding="utf-8")
SPEC_TEXT = SPEC + PROTO

# Names that are protocol identity rather than policy: changing them changes what the tool IS,
# not how it behaves on a project. Reported separately, never as findings.
IDENTITY = {"MARKER", "HERE", "HOME", "CLAUDE_DIR", "PROJECTS_DIR", "PLANS_DIR", "SPEC_PATH",
            "ROOT", "RED", "YELLOW", "GREEN", "NA", "USAGE", "__doc__"}


def literal(node):
    """The value if this is a pure literal (str/num/tuple/list/set/dict of literals)."""
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError):
        return None


def flatten(v):
    if isinstance(v, str):
        return [v]
    if isinstance(v, (list, tuple, set, frozenset)):
        return [x for i in v for x in flatten(i)]
    if isinstance(v, dict):
        return [x for i in list(v.keys()) + list(v.values()) for x in flatten(i)]
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return [str(v)]
    return []


def declared_in_spec(value) -> bool:
    parts = flatten(value)
    if not parts:
        return False
    return all(re.search(re.escape(p), SPEC_TEXT) for p in parts if p.strip())


rows = []
for path in sorted((ROOT / "scripts").glob("*.py")):
    if path.name.startswith("test-"):
        continue
    tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
    for stmt in tree.body:
        if not isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            continue
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        if not names or not stmt.value:
            continue
        val = literal(stmt.value)
        if val is None or isinstance(val, bool):
            continue
        name = names[0]
        kind = "identity" if name in IDENTITY else (
            "in spec" if declared_in_spec(val) else "CODE ONLY")
        rows.append((kind, f"{path.name}:{stmt.lineno}", name, repr(val)[:72]))

order = {"CODE ONLY": 0, "in spec": 1, "identity": 2}
for kind, where, name, val in sorted(rows, key=lambda r: (order[r[0]], r[1])):
    print(f"{kind:10}  {where:28}  {name:24}  {val}")
print()
print(f"{sum(1 for r in rows if r[0] == 'CODE ONLY')} code-only of {len(rows)} module constants")
