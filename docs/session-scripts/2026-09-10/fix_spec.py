import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/spec/project-standard.yaml")
old = """        still_unverified: >
          None of this has run on a real Windows or macOS machine. It is documentation plus
          binary strings, which is better than assumption and worse than a test.
"""
new = """        verified_2026_09_10: >
          BOTH shims have now run on the machines they were written for. The CI matrix added
          macos-latest and windows-latest, and hooks/rite.ps1 executed for the first time
          anywhere and passed. What this replaces was the claim "none of this has run on a real
          Windows or macOS machine", which stopped being true on 2026-09-10 — the day CI first
          ran three platforms.
        still_unverified: >
          The .ps1 shim is exercised by CI directly and by NOTHING in production:
          hooks/hooks.json names `bash rite.sh` for all three events and never references it.
          Windows without Git for Windows — the fourth row of `coverage` above — therefore has
          no working hook, and the gate that passes is not evidence that the path works.
          See c-rite-ps1-unreachable-in-production.
"""
text = p.read_text(encoding="utf-8")
if text.count(old) != 1:
    sys.exit(f"ABORT: matched {text.count(old)} times, expected 1")
before = len(text.encode("utf-8"))
p.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
print(f"project-standard.yaml: {before} -> {len(p.read_bytes())} bytes")
