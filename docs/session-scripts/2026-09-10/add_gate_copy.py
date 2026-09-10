import pathlib, sys
p = pathlib.Path(".github/gates.yaml")
t = p.read_text(encoding="utf-8")
anchor = "  - id: scaffold"
new = '''  - id: copy-attribution
    command: [scripts/test-copy-attribution.py]
    what: "a plan is attributed by authorship — a Write or ExitPlanMode naming it — never by mention"
    # Encodes a defect that shipped for twenty minutes: the first attributor matched any
    # occurrence of the plan's path, and the session BUILDING it had listed the plans directory,
    # so rite's transcript mentioned every plan on the machine. Five of thirteen mis-attributed.
    # Synthetic fixtures only — it never reads real transcripts.

  - id: scaffold'''
if t.count(anchor) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(anchor, new, 1), encoding="utf-8", newline="\n")
print("gate registered")
