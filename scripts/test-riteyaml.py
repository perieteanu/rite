#!/usr/bin/env python3
"""Differential test: riteyaml must parse this project's YAML identically to PyYAML.

This test IS the correctness claim for scripts/riteyaml.py. PyYAML is the ORACLE here, never
a runtime dependency — it is used to prove the replacement and then not shipped.

Per d-stdlib-only-yaml-subset: if this cannot be made to pass, the correct response is to
revert to PyYAML, not to weaken the test.

THREE CLASSES OF SNIPPET, because a refusal is not one thing. Rite now checks every YAML file a
project carries, not only its own artifacts, and the verdict differs by kind: a file that is not
YAML is the project's defect (RED), while valid YAML using a construct outside Rite's declared
subset is a conformance note (YELLOW). A single error class carrying both would make the checker
unable to tell them apart.

  MUST_SUPPORT        the oracle accepts, and riteyaml returns the SAME structure
  MUST_REFUSE         the oracle ACCEPTS and riteyaml raises YamlUnsupported — valid YAML,
                      outside the declared subset
  MUST_REJECT_INVALID the oracle REJECTS and riteyaml raises YamlInvalid — not YAML at all

THE ORACLE DECIDES THE CLASS, not the author of the case. Every case asserts PyYAML's verdict as
well as riteyaml's, so a snippet filed under the wrong heading fails here rather than shipping a
wrong kind. `safe_load_all` is the oracle, not `safe_load`: a multi-document stream is valid YAML
that `safe_load` refuses, and classifying it as invalid on that basis would be wrong.

WITHOUT PyYAML the oracle half is skipped and the rest STILL RUNS — the kinds, the construct ids,
and their parity with the spec are all checkable without it. Only the comparisons that need an
oracle are skipped, and the exit code says which happened.

Run:  python scripts/test-riteyaml.py
Exit: 0 pass · 1 fail · 2 the oracle half was skipped (PyYAML absent)
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import riteyaml  # noqa: E402
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

try:
    import yaml  # the oracle
    HAVE_ORACLE = True
except ImportError:
    HAVE_ORACLE = False


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

# Constructs the parser must SUPPORT, each proven against PyYAML rather than against a
# hand-written expectation. Block literals, flow mappings and chomping indicators were all in
# MUST_REFUSE until 2026-09-09, when the first run against outside projects showed real files
# using them: hwprivacy's ROADMAP and DECISIONS use `|`, plumbing's ROADMAP and ARCHITECTURE
# use `{...}`. The original subset was measured on this repo alone — a sample of one, treated
# as a population. See c-yaml-subset-too-narrow-for-the-wild.
MUST_SUPPORT = {
    "block literal": "text: |\n  line one\n  line two\n",
    "block literal, strip": "text: |-\n  no trailing newline\n",
    "block literal, keep": "text: |+\n  keep the blanks\n\n\n",
    "block literal, blank line inside": "text: |\n  first\n\n  third\n",
    "block literal, deeper indent kept": "text: |\n  outer\n    inner\n",
    "block literal in a sequence": "s:\n  - |\n    one\n  - |\n    two\n",
    "folded, strip": "text: >-\n  folded and\n  stripped\n",
    "folded, keep": "text: >+\n  folded, kept\n\n",
    "flow mapping": "a: {b: 1}\n",
    "flow mapping, empty": "a: {}\n",
    "flow mapping, quoted value with comma": 'a: {b: "x, y", c: 2}\n',
    "flow mapping, nested": "a: {b: [1, 2], c: {d: 3}}\n",
    "flow mapping in a sequence": "s:\n  - {a: 1}\n  - {b: 2}\n",
    "flow mapping, colon inside a quoted value": 'a: {b: "k: v"}\n',

    # ── added 2026-09-12, all found by measuring 478 real files ────────────────
    # SIX REAL FILES used a quoted scalar continued onto a second line and were refused as
    # "unterminated" — a false RED on valid YAML, and the single largest gap the measurement
    # found. Folding is PyYAML's, not invented here: a line break becomes a space, a blank line
    # becomes a newline, trailing white space is discarded, and a trailing backslash in a
    # double-quoted scalar escapes the break entirely.
    "double-quoted, continued": 'a: "one\n  two"\n',
    "single-quoted, continued": "a: 'one\n  two'\n",
    "double-quoted, blank line inside": 'a: "one\n\n  two"\n',
    "double-quoted, escaped line break": 'a: "one\\\n  two"\n',
    "double-quoted, escaped break after a space": 'a: "one \\\n  two"\n',
    "double-quoted, trailing white space discarded": 'a: "one   \n  two"\n',
    "double-quoted, escaped backslash at end of line": 'a: "one\\\\\n  two"\n',
    "single-quoted, doubled quote at end of line": "a: 'it''\n  s'\n",
    "quoted, continued, in a sequence": '- "one\n  two"\n- x\n',
    "quoted, continued inside a flow sequence": 'a: ["x\n  y"]\n',
    # A continuation may be indented LESS than the key that started it. PyYAML allows it, so
    # refusing it would be Rite inventing a rule.
    "quoted, continuation at column 0": 'a: "x\ny"\n',

    # An indicator only opens a node at the START of one. In the middle of a plain scalar it is
    # ordinary text, and the line-based refusal regex used until 2026-09-12 rejected both of
    # these — valid YAML, refused, in files nobody had run the parser over.
    "ampersand inside a plain scalar": "a: see &ref here\n",
    "asterisk inside a plain scalar": "a: x *y z\n",
    "colon without a space is not a mapping": "a: x:y\n",
    "a URL in a plain scalar": "a: http://x.y/z\n",
    "quoted key containing a colon": '"a: b": 1\n',

    # Real-world shapes that must not be mistaken for defects.
    "leading byte order mark": "\ufeffa: 1\n",
    "CRLF line endings": "a: 1\r\nb: 2\r\n",
    "leading document marker": "---\na: 1\n",
    "document end marker": "a: 1\n...\n",
    "document end marker then a comment": "a: 1\n...\n# done\n",
}

# Valid YAML that is OUTSIDE the declared subset. Refusing is correct; the point of the class is
# that it is refused as `unsupported`, so the checker reports a conformance note rather than
# calling someone's working file broken.
#
# `construct` is the id the parser attaches to the refusal, and the same id the spec declares in
# `yaml_subset`. The parity assertion below is what stops the two lists drifting apart.
MUST_REFUSE = {
    "anchor": ("base: &defaults\n  a: 1\n", "anchor"),
    "anchor and alias": ("a: &x 1\nb: *x\n", "anchor"),
    "tag": ("when: !!timestamp 2026-09-08\n", "tag"),
    "non-specific tag": ("a: ! x\n", "tag"),
    "merge key": ("a:\n  <<: {b: 1}\n  c: 2\n", "merge_key"),
    "complex key": ("? a\n: value\n", "complex_key"),
    "ambiguous boolean": ("enabled: yes\n", "ambiguous_boolean"),
    "ambiguous boolean as a key": ("on: push\n", "ambiguous_boolean"),
    "flow mapping that is really a set": ("a: {b, c}\n", "flow_set"),
    # Valid as a STREAM, which is why the oracle here is safe_load_all. Rite reads one document
    # per file everywhere, so silently merging two was a wrong answer rather than a limitation.
    "multi-document stream": ("a: 1\n---\nb: 2\n", "multi_document"),
    "trailing document marker": ("a: 1\n---\n", "multi_document"),
    # PyYAML folds this into the single string "a - b". It is valid, and it is almost always a
    # nested list whose parent key was forgotten — so it is reported, not guessed at.
    "list under a plain sequence item": ("- a\n  - b\n", "nested_list_under_plain_item"),
    "list under a plain mapping value": ("k: a\n  - b\n", "nested_list_under_plain_item"),
}

# NOT YAML. The oracle rejects every one of these, and riteyaml must too — this is the class that
# makes `rite check` able to say a project's file is broken.
#
# TEN OF THE TWELVE FALSE ACCEPTS measured on 2026-09-11 were the first case here: a plain scalar
# containing ": ", which YAML forbids and riteyaml read as text. The rest of this class is the
# remainder of that measurement plus the probe that followed it.
MUST_REJECT_INVALID = {
    "plain scalar containing a colon and space":
        ("a: x: y\n", "mapping_value_in_plain_scalar"),
    "plain scalar ending in a colon":
        ("a: see below:\n", "mapping_value_in_plain_scalar"),
    "sequence item containing a colon and space":
        ("- x: y: z\n", "mapping_value_in_plain_scalar"),
    "a more-indented key after a plain value":
        ("a: first\n  second: part\n", "bad_indentation"),
    "over-indented key": ("a:\n  b: 1\n   c: 2\n", "bad_indentation"),
    "sequence under a quoted item": ("- 'a'\n  - b\n", "bad_indentation"),
    "alias with no anchor defined": ("a: *nope\n", "undefined_alias"),
    "asterisk that is not an alias name": ("- *.log files\n", "reserved_indicator"),
    "ampersand with no anchor name": ("a: & b\n", "reserved_indicator"),
    "at sign starting a plain scalar": ("a: @x\n", "reserved_indicator"),
    "backtick starting a plain scalar": ("a: `x`\n", "reserved_indicator"),
    "percent starting a plain scalar": ("a: %x\n", "reserved_indicator"),
    "tab indentation": ("a:\n\tb: 1\n", "tab_indentation"),
    "tab after a space": ("a:\n \tb: 1\n", "tab_indentation"),
    "tab in a plain continuation": ("a: x\n \ty\n", "tab_indentation"),
    # Both directions of the same defect: the root structure ends and the file keeps going. Until
    # 2026-09-12 the parser returned what it had and SILENTLY DROPPED the rest, which is the
    # worst failure available to it — a truncated document that reads as a complete one.
    "mapping then a root sequence": ("a: 1\n- b\n", "content_after_root"),
    "sequence then a root mapping": ("- a\nb: 1\n", "content_after_root"),
    "root indented, then column 0": ("  a: 1\nb: 2\n", "content_after_root"),
    "a line that is not a key": ("a: 1\nnot a key\n", "expected_key_value"),
    "unterminated double quote": ('a: "one\n', "unterminated_quote"),
    "unterminated single quote": ("a: 'one\n", "unterminated_quote"),
    "document marker inside a quoted scalar": ('a: "x\n---\ny"\n', "unterminated_quote"),
    "text after a closing quote": ('a: "x" y\n', "text_after_quote"),
    "unterminated flow mapping": ("a: {b: 1\n", "unterminated_flow"),
    "unterminated flow sequence": ("a: [1, 2\n", "unterminated_flow"),
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


def oracle_accepts(snippet: str) -> bool:
    """Is this valid YAML at all? safe_load_all, because a multi-document stream is valid."""
    try:
        list(yaml.safe_load_all(snippet))
    except yaml.YAMLError:
        return False
    return True


def declared_constructs() -> tuple[dict[str, str], str | None]:
    """{construct: kind} as spec/project-standard.yaml declares it, or a reason it is missing.

    THE SPEC IS THE AUTHORITY AND THIS IS THE PARITY CHECK. The parser reads nothing from the
    spec at runtime — it stays a standalone module — so without a check the refusal table and the
    published standard would be two hand-maintained lists free to drift. That is the failure this
    project exists to attack, and it would be self-inflicted.
    """
    path = ROOT / "spec" / "project-standard.yaml"
    try:
        spec = riteyaml.load(path.read_text(encoding="utf-8"), str(path))
    except (OSError, riteyaml.RiteYamlError) as exc:
        return {}, f"cannot read the standard: {exc}"
    section = spec.get("yaml_subset")
    if not isinstance(section, dict):
        return {}, "the standard declares no `yaml_subset` section"
    out: dict[str, str] = {}
    for key, kind in (("refused", "unsupported"), ("rejected_as_invalid", "invalid")):
        for item in section.get(key) or []:
            if isinstance(item, dict) and item.get("construct"):
                out[str(item["construct"])] = kind
    return out, None


def main() -> int:
    failures: list[str] = []

    # ── the half that needs no oracle: kinds, construct ids, and parity with the spec ──
    raised: dict[str, str] = {}
    for kind, cases in (("unsupported", MUST_REFUSE), ("invalid", MUST_REJECT_INVALID)):
        want_class = riteyaml.YamlUnsupported if kind == "unsupported" else riteyaml.YamlInvalid
        for name, (snippet, construct) in cases.items():
            try:
                riteyaml.load(snippet, f"<{name}>")
            except riteyaml.RiteYamlError as e:
                if not isinstance(e, want_class):
                    failures.append(f"{name}: raised {type(e).__name__}, expected "
                                    f"{want_class.__name__} — the KIND is what the checker's "
                                    f"verdict turns on")
                if getattr(e, "construct", None) != construct:
                    failures.append(f"{name}: construct {getattr(e, 'construct', None)!r}, "
                                    f"expected {construct!r}")
                else:
                    raised[construct] = kind
            else:
                failures.append(f"did NOT refuse {name} — it guessed instead")

    declared, why_not = declared_constructs()
    if why_not:
        failures.append(f"parity with the standard cannot be checked: {why_not}")
    else:
        for construct, kind in sorted(raised.items()):
            if construct not in declared:
                failures.append(f"the parser raises {construct!r} and the standard does not "
                                f"declare it — a refusal nobody can look up")
            elif declared[construct] != kind:
                failures.append(f"{construct!r} is {kind} here and "
                                f"{declared[construct]} in the standard")
        for construct in sorted(declared):
            if construct not in raised:
                failures.append(f"the standard declares {construct!r} and no case here raises "
                                f"it — a declaration nothing proves")

    if not HAVE_ORACLE:
        if failures:
            print(f"FAIL  {len(failures)} problem(s) in the oracle-free half\n")
            for f in failures:
                print(" ", f)
            return 1
        print("SKIP  PyYAML is not installed — it is the oracle for this test, not a dependency.")
        print(f"      The oracle-free half PASSED: {len(raised)} construct(s) raise the declared "
              f"kind and match the standard.")
        print("      Install it to verify the structures themselves: pip install pyyaml")
        return 2

    # ── the oracle half ───────────────────────────────────────────────────────
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

    # The support half. Each construct is compared against the ORACLE, never against a
    # hand-written expectation — the point is that we match PyYAML, not that we match a guess.
    supported = 0
    for name, snippet in MUST_SUPPORT.items():
        expected = yaml.safe_load(snippet)
        try:
            got = riteyaml.load(snippet, f"<{name}>")
        except riteyaml.RiteYamlError as e:
            failures.append(f"refused {name}, which is inside the subset -> {e}")
            continue
        diffs = list(differences(expected, got))
        supported += 1
        if diffs:
            failures.append(f"{name}: {len(diffs)} difference(s) from PyYAML")
            failures.extend("    " + d for d in diffs[:4])

    # THE ORACLE DECIDES THE CLASS. A case filed under the wrong heading is a wrong verdict
    # waiting to ship: `unsupported` promises the file is valid YAML, and `invalid` promises it
    # is not. Neither promise is ours to make.
    for name, (snippet, _) in MUST_REFUSE.items():
        if not oracle_accepts(snippet):
            failures.append(f"{name} is in MUST_REFUSE, but PyYAML rejects it — it is INVALID, "
                            f"not merely outside the subset")
    for name, (snippet, _) in MUST_REJECT_INVALID.items():
        if oracle_accepts(snippet):
            failures.append(f"{name} is in MUST_REJECT_INVALID, but PyYAML ACCEPTS it — "
                            f"refusing it as invalid would call a working file broken")

    if failures:
        print(f"FAIL  {len(failures)} problem(s)\n")
        for f in failures:
            print(" ", f)
        return 1

    print(f"PASS  {checked} document(s) + {supported}/{len(MUST_SUPPORT)} in-subset constructs "
          f"parsed identically to PyYAML;\n"
          f"      {len(MUST_REFUSE)} valid-but-unsupported and {len(MUST_REJECT_INVALID)} invalid "
          f"snippets refused with the right kind,\n"
          f"      across {len(raised)} construct(s), every one declared in the standard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
