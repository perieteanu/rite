import pathlib, sys

# 1 — declare the test on ARCHITECTURE
s = pathlib.Path("spec/project-standard.yaml")
t = s.read_text(encoding="utf-8")
old = '''      - level: populated
        rule: min_content_sections
        value: 3
        means: >
          At least three H2 sections beyond the title. This replaces a required-key list,
          which cannot span a Rust codebase and a plumbing schematic.
'''
new = '''      - level: populated
        rule: min_content_sections
        value: 3
        means: >
          At least three H2 sections beyond the title. This replaces a required-key list,
          which cannot span a Rust codebase and a plumbing schematic.
      - level: populated
        rule: required_any_of_sections
        means: >
          One of the topology sections, honouring `section_aliases` — "Summary" satisfies
          "Shape". DECLARED 2026-09-10: the rule had been implemented since the checker was
          written and invoked by NOTHING, because `required_any_of_sections` appeared only
          under `structure:` as data and no artifact listed it under `tests:`. Dead code in the
          checker whose whole subject is rules nobody runs.
          YELLOW, never RED, and `required_any_of_waived_when` says why: a non-code project
          whose top-level keys ARE the topology has no generic container section, and
          d-noncode-first-class makes those first-class. The finding names the waiver so a
          reader can dismiss it deliberately rather than wonder.
'''
if t.count(old) != 1:
    sys.exit("ABORT spec")
s.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("  ok  declared")

# 2 — honour the aliases the spec already declares
c = pathlib.Path("scripts/rite-check.py")
t = c.read_text(encoding="utf-8")
old_rule = '''@rule("required_any_of_sections")
def _required_any_of(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    want = (art.get("structure") or {}).get("required_any_of_sections") or []
    have = {s.lower() for s in sections(text)}
    return (GREEN, "satisfied") if any(w.lower() in have for w in want) \\
        else (YELLOW, "none of: " + ", ".join(want))'''
new_rule = '''@rule("required_any_of_sections")
def _required_any_of(ctx, art, test):
    """One of the declared topology sections, counting declared aliases.

    THE ALIASES WERE BEING IGNORED. `section_aliases` sits in the same `structure:` block and
    says "Summary" satisfies "Shape"; the rule compared against the primary names only, so a
    document doing exactly what the spec permits would have been reported as missing all of
    them. Never noticed, because until 2026-09-10 no artifact declared this rule and it had
    never run on anything.
    """
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    structure = art.get("structure") or {}
    want = structure.get("required_any_of_sections") or []
    if not want:
        return NA, "the artifact declares no required_any_of_sections"
    aliases = structure.get("section_aliases") or {}
    have = {s.lower() for s in sections(text)}
    for primary in want:
        accepted = [primary, *(aliases.get(primary) or [])]
        if any(a.lower() in have for a in accepted):
            return GREEN, f"{primary} present" if primary.lower() in have \\
                else f"satisfied by an alias of {primary}"
    waived = structure.get("required_any_of_waived_when")
    note = " — waived where the top-level keys ARE the topology" if waived else ""
    return YELLOW, "none of: " + ", ".join(want) + note'''
if t.count(old_rule) != 1:
    sys.exit("ABORT rule")
c.write_text(t.replace(old_rule, new_rule, 1), encoding="utf-8", newline="\n")
print("  ok  aliases honoured")
