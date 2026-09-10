import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/spec/project-standard.yaml")
anchor = "# ── write discipline (CORE) ─"
text = p.read_text(encoding="utf-8")
i = text.find(anchor)
if i == -1:
    sys.exit("ABORT: write-discipline anchor not found")

block = '''# ── generated blocks (CORE — Rite's own) ─────────────────────────────
# WHERE THIS FILE'S DATA IS WRITTEN INTO A HAND-WRITTEN DOCUMENT, and kept true by a check.
#
# PROJECT-STANDARD.md is generated whole, so it cannot drift. README.md cannot be: it is prose
# a human writes, which happens to contain one table this file owns. On 2026-09-10 that table
# was hand-copied into README.md, template/.rite.yaml and CLAUDE.md on the same day the
# mechanism it describes was built — four copies, three hand-maintained, introduced by the
# project whose thesis is that such copies rot (c-stage-table-duplicated-in-three-places).
#
# A block names its generator and its targets. `render-standard.py --blocks` fills every one;
# `--blocks --check` fails on any that has drifted, and that is the completion test. The
# markers are inert to both Markdown and YAML, so a rendered README shows the table and a
# parsed .rite.yaml sees comments.
#
# WHY THE LIST LIVES HERE rather than in the renderer: a path list that exists only in code is
# a hardcoded value with no human-visible home. This file is already the authority for what is
# generated, so it is the authority for where.
generated_blocks:
  layer: core
  markers:
    md: ["<!-- rite:generated {id} -->", "<!-- /rite:generated -->"]
    yaml_comment: ["# rite:generated {id}", "# /rite:generated"]
  blocks:
    - id: stage-table
      what: "Which artifacts each stage adds, from artifacts[].required_from_stage"
      source: "stage_vocabulary.values for the order; artifacts[].required_from_stage for the rows"
      targets:
        - path: README.md
          style: md
        - path: template/.rite.yaml
          style: yaml_comment
      not_targeted:
        CLAUDE.md: >
          Its copy was DELETED on 2026-09-10 rather than generated. The mapping was a prose
          sentence mid-bullet, and a marker block there would have forced a table into a
          document that is dense prose by design. Removing a copy beats mechanising it.

'''
before = len(text.encode("utf-8"))
p.write_text(text[:i] + block + text[i:], encoding="utf-8", newline="\n")
print(f"project-standard.yaml: {before} -> {len(p.read_bytes())} bytes")
