#!/usr/bin/env python3
"""Completion test: a documentation path is never a literal.

WHY THIS GATE EXISTS, measured rather than supposed. On 2026-09-12 an audit asked of every
module constant in scripts/ not "does this value appear in the spec" but "does the code READ it
from the spec", and the answer for rite_copy.py and rite_init.py was NOTHING. Every destination
they wrote was re-typed from a value spec/project-standard.yaml already declares:

    spec: path: "docs/claude-memory.md"            code: DOCS + MIRROR_NAME
    spec: path: "docs/session-scripts/<ISO>/..."   code: DOCS + SCRIPTS_SUBDIR + its own format
    spec: plan_copy path                           code: built inline in copy_plans

So the PRODUCER of three artifacts and the CHECKER of those same three artifacts held
independent copies of each path, which is exactly the drift riterules.py was extracted to
prevent — and why `canonical_name` could pass while the copier wrote somewhere else. The same
audit found `"docs"` re-typed three times (two of the lines byte-identical) and the format pair
("yaml", "md") twice more.

THE RULE IS NORMATIVE AND WAS ENFORCED BY NOTHING, which is the class of failure this whole
project is about. Costin's standing instruction — no hardcoded values unless declared in a
human-visible settings file — had no completion test here, so it survived being read many times.

WHAT IS A VIOLATION, and the line is drawn at OPERATIONAL versus EXPLANATORY:

  half A, scripts/*.py   An operational string literal naming a documentation directory or a
                         path beneath one. Docstrings are exempt: a docstring is prose for a
                         reader, the same standing the skills' fallback text has below. One
                         last-resort fallback is allowed, in riterules.py alone, and this gate
                         asserts it appears exactly once anywhere.

  half B, skills/*.md    A skill prompt is a command an agent RUNS, so a path it names that the
                         project does not have sends the agent to edit a file that is not there.
                         The canonical names are allowed to STAY as the degradation path for a
                         user with disableSkillShellExecution set — but only if the prompt also
                         injects the resolver, so the reader always receives the project's real
                         paths first. Naming paths WITHOUT the resolver is the violation.

The vocabulary is not hardcoded here either: the directory names and the artifact paths are read
from spec/project-standard.yaml at run time, so adding an artifact extends this gate for free.

WHAT THIS GATE CANNOT SEE, stated because a checker that implies coverage it lacks is the thing
this project attacks. The format alternatives — the pair ("yaml", "md") that rite-check.py used
to carry twice — are NOT policed here. Those two strings occur legitimately all over a codebase
that reads both formats, so a scan for them would be noise, and noise is what gets a gate
switched off. Their protection is different in kind: they now have a declared home under
local.docs_dir.formats, and the checker reads it. If someone re-types them, this gate stays
green and only review catches it.

Run:  python scripts/test-docs-path-literals.py
Exit: 0 pass · 1 a violation
"""

from __future__ import annotations

import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import riteyaml  # noqa: E402

ritefs.use_utf8_stdio()

SPEC_PATH = ROOT / "spec" / "project-standard.yaml"

# The ONE permitted last-resort fallback, and where it is permitted to live. Everything else must
# call the resolver. Asserted UNIQUE below, because "one fallback" stops being true the moment a
# second file copies it — which is how the three re-typed "docs" came about in the first place.
FALLBACK_OWNER = "riterules.py"

# Entry points and libraries. Tests are excluded: a test asserting a path is asserting the
# expected VALUE, which is its job.
def code_files() -> list[pathlib.Path]:
    return [p for p in sorted((ROOT / "scripts").glob("*.py"))
            if not p.name.startswith("test-")]


def skill_files() -> list[pathlib.Path]:
    return sorted(ROOT.glob("skills/*/SKILL.md"))


def vocabulary(spec: dict) -> tuple[list[str], list[str], list[str]]:
    """(documentation directory names, paths beneath one, the components of those paths).

    Root-level artifacts (LOG.md, HANDOFF.md, README.md, CLAUDE.md, LICENSE) are deliberately
    OUT of scope: they do not move when a project declares a different documentation directory,
    so naming them is not the defect this rule is about.

    COMPONENTS ARE THE THIRD CLASS, and leaving them out is how the first version of this gate
    missed the two constants that prompted it. `MIRROR_NAME = "claude-memory.md"` and
    `SCRIPTS_SUBDIR = "session-scripts"` contain no directory name at all — they become a
    documentation path only once joined, so a scan for "docs/" never sees them while the value
    is every bit as re-typed. Placeholders (<ISO date>, <name>, *) are not values and are
    dropped.
    """
    local = (spec.get("local") or {}).get("docs_dir") or {}
    dirs = [d for d in [local.get("default"), *(local.get("alternatives") or [])] if d]
    paths = []
    for art in spec.get("artifacts") or []:
        for key in ("path", "path_pattern"):
            value = art.get(key)
            if isinstance(value, str) and any(value.startswith(f"{d}/") for d in dirs):
                paths.append(value)
    components = {
        part
        for p in paths
        for part in p.split("/")[1:]
        if part and "<" not in part and "*" not in part
    }
    return dirs, sorted(set(paths)), sorted(components)


def docstring_nodes(tree: ast.Module) -> set[int]:
    """id() of every Constant that is a docstring, so the scan can skip prose."""
    out = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef,
                                 ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None) or []
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            out.add(id(body[0].value))
    return out


def offending_literals(tree: ast.Module, dirs: list[str], components: list[str]):
    """Operational string literals naming a documentation directory, a path beneath one, or a
    component of such a path. Yields (lineno, text, what_it_matched, is_bare_dir)."""
    skip = docstring_nodes(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if id(node) in skip:
            continue
        text = node.value
        matched = next((d for d in dirs
                        if text == d or text.startswith(f"{d}/") or f"/{d}/" in text), None)
        if matched is not None:
            yield node.lineno, text, matched, text == matched
            continue
        if text in components:
            yield node.lineno, text, text, False


def main() -> int:
    try:
        spec = riteyaml.load(SPEC_PATH.read_text(encoding="utf-8"), str(SPEC_PATH))
    except (OSError, riteyaml.RiteYamlError) as exc:
        print(f"FAIL  cannot read the standard: {exc}")
        return 1

    dirs, declared_paths, components = vocabulary(spec)
    if not dirs:
        print("FAIL  spec declares no local.docs_dir — this gate has no vocabulary to work from.")
        return 1

    failures: list[str] = []
    fallback_sites: list[str] = []
    checked_code = 0

    # ── half A: operational literals in code ─────────────────────────────────
    for path in code_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), rel)
        except (OSError, SyntaxError) as exc:
            failures.append(f"{rel}: cannot parse — {exc}")
            continue
        checked_code += 1
        for lineno, text, matched, is_bare_dir in offending_literals(tree, dirs, components):
            site = f"{rel}:{lineno}"
            if is_bare_dir and path.name == FALLBACK_OWNER:
                fallback_sites.append(site)
                continue
            what = ("names the documentation directory" if is_bare_dir
                    else f"is part of a path the spec declares ({matched})")
            failures.append(
                f"{site}: {text!r} {what}. Resolve it through riterules instead — the spec "
                f"owns local.docs_dir and each artifact's `path`, and a project may declare "
                f"its own documentation directory."
            )

    if len(fallback_sites) > 1:
        failures.append(
            f"the last-resort fallback appears {len(fallback_sites)} times "
            f"({', '.join(fallback_sites)}). It is permitted ONCE, in {FALLBACK_OWNER}: "
            f"a second copy is free to disagree with the first."
        )

    # ── half B: skill prompts must inject the resolver if they name paths ────
    checked_skills = 0
    for path in skill_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append(f"{rel}: cannot read — {exc}")
            continue
        checked_skills += 1
        named = sorted({p for p in declared_paths if p in text}
                       | {f"{d}/" for d in dirs if f"{d}/" in text})
        if not named:
            continue
        if "rite.sh\" paths" in text or "rite.sh' paths" in text or "rite.ps1 paths" in text:
            continue
        failures.append(
            f"{rel}: names {', '.join(sorted(named)[:4])} but never injects the resolver. "
            f"A skill prompt is a command an agent runs, so on a project using a different "
            f"documentation directory it sends the agent to files that do not exist. Add the "
            f"resolver injection; the canonical names may stay as the degradation path."
        )

    if failures:
        print(f"FAIL  {len(failures)} documentation path(s) written as a literal:")
        for f in failures:
            print(f"        {f}")
        print()
        print("      The spec owns these values — local.docs_dir and each artifact's `path`.")
        print("      Code reads them through riterules; prompts receive them from the resolver.")
        return 1

    print(f"PASS  {checked_code} module(s) name no documentation directory "
          f"({len(fallback_sites)} permitted fallback); "
          f"{checked_skills} skill prompt(s) resolve their paths; "
          f"{len(declared_paths)} declared path(s) in the vocabulary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
