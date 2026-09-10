import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/docs/ROADMAP.yaml")
old = """  declares required_from_stage, and a project is not asked for what its stage has not reached:
  idea wants LOG and HANDOFF, spec adds README/CLAUDE.md/MISSION/ROADMAP, build adds
  ARCHITECTURE/CONVENTIONS/DECISIONS, shipped adds LICENSE. Measured before: an empty project
"""
new = """  declares required_from_stage, and a project is not asked for what its stage has not reached.
  THE MAPPING IS NOT REPEATED HERE and this sentence is the reason why: it used to be, and that
  made a fourth hand-maintained copy alongside README, template/.rite.yaml and CLAUDE.md. It
  now has one home in the spec, is generated into README and the template as a rite:generated
  block, and a guard fails if a fifth copy appears. Measured before: an empty project
"""
text = p.read_text(encoding="utf-8")
if text.count(old) != 1:
    sys.exit(f"ABORT: matched {text.count(old)} times, expected 1")
before = len(text.encode("utf-8"))
p.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
print(f"ROADMAP.yaml: {before} -> {len(p.read_bytes())} bytes")
