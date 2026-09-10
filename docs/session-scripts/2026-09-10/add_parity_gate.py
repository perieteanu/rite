import pathlib, sys
p = pathlib.Path(".github/gates.yaml")
t = p.read_text(encoding="utf-8")
anchor = "  - id: copy-attribution"
new = '''  - id: mirror-port-parity
    command: [scripts/test-mirror-port-parity.py]
    what: "rite's memory mirror still renders identically to the script it ported"
    skip_means: >
      ~/.claude/scripts/claude-mirror-memory.py is not on this machine, so there is nothing to
      compare against. A CI runner has never had it, and this is also the END STATE: the
      original was kept deliberately as a fallback while rite is on trial, and when it is
      retired this gate skips forever. DELETE IT AT THAT POINT — a gate that can no longer fail
      is not a gate — along with the parity sentence in ~/.claude/commands/mirror-memory.md.
    # Two implementations of one output are alive at once, on purpose. "They agree" was checked
    # twice by hand and by nothing else, which is precisely the kind of claim this project
    # refuses to accept from anyone else. It compares the two GENERATORS and writes nothing.

  - id: copy-attribution'''
if t.count(anchor) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(anchor, new, 1), encoding="utf-8", newline="\n")
print("registered")
