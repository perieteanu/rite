#!/usr/bin/env python3
"""Completion test for the portability rules that govern PIPES and stdio.

WHY THIS EXISTS, AND WHY IT EXISTS TODAY. On 2026-09-10 the matrix run added
process_output_declares_encoding to the standard, and within the hour that rule was found to
be violated in FIVE of the repo's seven subprocess.run call sites — including two inside
rite-check.py, which is the checker itself. One of them produced a RED on Windows only,
accusing an untouched milestone of having been rewritten.

Those five were found by grepping. That is the failure this project exists to abolish: a rule
whose only enforcement is somebody remembering to look. The rule was normative and unchecked
for exactly as long as it took to write it down.

WHAT IT CHECKS, both halves of one pipe:

  1. WRITING — every module that prints declares its stdio as UTF-8 first, at module level,
     via ritefs.use_utf8_stdio(). Python selects the console codepage on Windows, so `·` and
     `—` go out as cp1252 there and UTF-8 everywhere else.

  2. READING — every subprocess.run() names BOTH encoding="utf-8" AND errors="replace". The
     encoding is what makes the bytes mean the same thing at both ends; errors="replace" is
     what turns a future violation into visible mojibake rather than a UnicodeDecodeError in
     a reader thread, which reports the wrong component as broken.

AST, NEVER GREP, and the reason is concrete rather than stylistic. A substring search for
"use_utf8_stdio()" matches the DEFINITION in ritefs.py and matches this docstring, so it would
clear a file that never calls it and would have to be special-cased into unreliability. The
syntax tree distinguishes a call from a mention; text cannot.

Run:  python scripts/test-portability-rules.py
Exit: 0 pass · 1 fail
"""

from __future__ import annotations

import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

SCAN_DIRS = ("scripts", "spec", ".github")

# ritefs.py DEFINES use_utf8_stdio and prints nothing. A module that reconfigures global stdio
# on import would be a library with a side effect, so the rule is deliberately about entry
# points; riteyaml.py is exempt for the same reason and needs no naming, since it never prints.
EXEMPT_FROM_STDIO_RULE = {"ritefs.py"}


def python_files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        out.extend(p for p in sorted(base.rglob("*.py")) if "__pycache__" not in p.parts)
    return out


def is_print_call(node: ast.AST) -> bool:
    """print(...) or sys.stdout.write(...) / sys.stderr.write(...)."""
    if not isinstance(node, ast.Call):
        return False
    fn = node.func
    if isinstance(fn, ast.Name) and fn.id == "print":
        return True
    # sys.stdout.write / sys.stderr.write
    if (isinstance(fn, ast.Attribute) and fn.attr == "write"
            and isinstance(fn.value, ast.Attribute)
            and fn.value.attr in {"stdout", "stderr"}):
        return True
    return False


def calls_utf8_declaration_at_module_level(tree: ast.Module) -> bool:
    """A bare `ritefs.use_utf8_stdio()` statement in the module body.

    Module level specifically: the declaration has to happen before anything prints, and a call
    buried in a function that may never run is not a declaration.
    """
    for stmt in tree.body:
        if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
            continue
        fn = stmt.value.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
        if name == "use_utf8_stdio":
            return True
    return False


def subprocess_run_calls(tree: ast.Module):
    """Every subprocess.run(...) node, with the keyword names it passes."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr == "run" and \
                isinstance(fn.value, ast.Name) and fn.value.id == "subprocess":
            yield node, {kw.arg for kw in node.keywords if kw.arg}


def main() -> int:
    failures: list[str] = []
    checked_files = checked_calls = 0

    for path in python_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            failures.append(f"{rel}: does not parse — {exc}")
            continue
        checked_files += 1

        # 1. the writing half
        prints = any(is_print_call(n) for n in ast.walk(tree))
        if prints and path.name not in EXEMPT_FROM_STDIO_RULE:
            if not calls_utf8_declaration_at_module_level(tree):
                failures.append(
                    f"{rel}: prints, but never calls ritefs.use_utf8_stdio() at module level. "
                    f"On Windows its output is written in the console codepage."
                )

        # 2. the reading half
        for node, kwargs in subprocess_run_calls(tree):
            checked_calls += 1
            missing = [k for k in ("encoding", "errors") if k not in kwargs]
            if missing:
                failures.append(
                    f"{rel}:{node.lineno}: subprocess.run() does not name "
                    f"{' and '.join(missing)}. A byte must not mean different things at the "
                    f"two ends of one pipe."
                )

    if failures:
        print(f"FAIL  {len(failures)} violation(s) of the portability rules:")
        for f in failures:
            print(f"        {f}")
        print()
        print("      See `portability` in spec/project-standard.yaml —")
        print("      process_output_declares_encoding.")
        return 1

    print(f"PASS  {checked_files} module(s) declare UTF-8 stdio where they print; "
          f"{checked_calls} subprocess.run call(s) name encoding and errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
