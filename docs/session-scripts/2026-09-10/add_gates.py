import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/.github/gates.yaml")
text = p.read_text(encoding="utf-8")

after_protocol = """  - id: riteyaml"""
blocks_gate = """  - id: blocks
    command: [spec/render-standard.py, --blocks, --check]
    what: "the stage table inside README and template/.rite.yaml still matches the spec"
    # PROJECT-STANDARD.md is generated whole and cannot drift. README.md is prose a human owns
    # that CONTAINS one table the spec owns, so the table is fenced by inert markers and
    # refilled. This gate is half of what retired c-stage-table-duplicated-in-three-places; the
    # other half is stage-table below, because generation cannot catch a copy that is not drift
    # from anything.

  - id: riteyaml"""

after_portability = """  - id: scaffold"""
guard_gate = """  - id: stage-table
    command: [scripts/test-stage-table-guard.py]
    what: "no document restates the stage mapping outside a rite:generated block"
    # The other half of the same fix. It reads the live, rewrite-only documents only: LOG.md,
    # DECISIONS.yaml and ROADMAP's milestones are append-only records of what was true then,
    # and a gate that fails on a file nobody may legally edit is a gate that gets switched off.

  - id: scaffold"""

for anchor, replacement in ((after_protocol, blocks_gate), (after_portability, guard_gate)):
    if text.count(anchor) != 1:
        sys.exit(f"ABORT: anchor {anchor!r} matched {text.count(anchor)} times")
    text = text.replace(anchor, replacement, 1)

before = len(p.read_bytes())
p.write_text(text, encoding="utf-8", newline="\n")
print(f"gates.yaml: {before} -> {len(p.read_bytes())} bytes")
