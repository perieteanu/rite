import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/CLAUDE.md")
old = """- **`LICENSE` is the one file that must NOT carry a provenance header.** It is third-party text
  reproduced verbatim; editing it changes its legal meaning. Required from stage `shipped`;
  rite declares `build`, so the check is NA until the commit that publishes.
- **STAGE gates the standard, not tier.** Every artifact declares `required_from_stage`, and a
  project is not asked for what its stage has not reached — `idea` wants LOG and HANDOFF,
  `spec` adds README/CLAUDE.md/MISSION/ROADMAP, `build` adds ARCHITECTURE/CONVENTIONS/DECISIONS,
  `shipped` adds LICENSE. **A declaration beats tier**; `tier` is now only a grouping label and
  the fallback when no stage is declared. **Deleting `stage:` does not make the standard
  lenient** — it reverts to the stricter tier behaviour, because absence is not a claim.
  See `d-stage-is-the-gating-axis`.
"""
new = """- **`LICENSE` is the one file that must NOT carry a provenance header.** It is third-party text
  reproduced verbatim; editing it changes its legal meaning. **`required_from_stage` gates
  whether an artifact is DEMANDED, not whether it is CHECKED when present** — LICENSE exists,
  so `min_lines` and `no_provenance_header` run and pass today at stage `build`. This bullet
  used to say the check "is NA until the commit that publishes", which was false and was caught
  on 2026-09-10 by running the checker against a `stage: shipped` copy. The stage decides only
  whether a MISSING LICENSE is RED or NA.
- **STAGE gates the standard, not tier.** Every artifact declares `required_from_stage`, and a
  project is not asked for what its stage has not reached. **The mapping is NOT repeated here** —
  it lives in `spec/project-standard.yaml` and is generated into README and `template/.rite.yaml`
  as a `rite:generated` block. This bullet used to enumerate it, which made a fourth
  hand-maintained copy; `spec/render-standard.py --blocks --check` and the stage-table guard
  are what replaced it. **A declaration beats tier**; `tier` is now only a grouping label and
  the fallback when no stage is declared. **Deleting `stage:` does not make the standard
  lenient** — it reverts to the stricter tier behaviour, because absence is not a claim.
  See `d-stage-is-the-gating-axis`.
"""
text = p.read_text(encoding="utf-8")
if text.count(old) != 1:
    sys.exit(f"ABORT: matched {text.count(old)} times, expected 1")
before = len(text.encode("utf-8"))
p.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
print(f"CLAUDE.md: {before} -> {len(p.read_bytes())} bytes")
