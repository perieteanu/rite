import pathlib, sys
p = pathlib.Path("spec/project-standard.yaml")
t = p.read_text(encoding="utf-8")
anchor = """      not_targeted:
        CLAUDE.md: >"""
new = """      not_targeted:
        CLAUDE.md: >"""
# append the two gate blocks after the stage-table block
tail_anchor = """          document that is dense prose by design. Removing a copy beats mechanising it.

"""
addition = """          document that is dense prose by design. Removing a copy beats mechanising it.

    - id: gate-counts
      what: "How many gates run, how many skip on a runner, and why — one sentence"
      source: "gates[] and gates[].skip_short in .github/gates.yaml"
      source_file: ".github/gates.yaml"
      targets:
        - path: README.md
          style: md
      not_targeted:
        CLAUDE.md and ROADMAP.current_state: >
          Their copies were DELETED on 2026-09-10 rather than generated. Neither reader needs
          the number — an agent reading CLAUDE.md and a session reading current_state both want
          to know WHERE the gates are declared, which is more durable than how many there are.
          Only the README's audience, a stranger deciding whether to care, is served by a count.

    - id: gate-list
      what: "Every gate, what it holds, and whether it runs on a CI runner"
      source: "gates[] in .github/gates.yaml"
      source_file: ".github/gates.yaml"
      targets:
        - path: docs/ARCHITECTURE.md
          style: md

"""
if t.count(tail_anchor) != 1:
    sys.exit(f"ABORT: matched {t.count(tail_anchor)}")
t = t.replace(tail_anchor, addition, 1)

# document source_file in the generated_blocks preamble
t = t.replace(
 "# A block names its generator and its targets. `render-standard.py --blocks` fills every one;",
 "# A block names its generator, its targets, and optionally the `source_file` it generates FROM\n"
 "# (default: this file). The gate blocks are fed from .github/gates.yaml, because that is the\n"
 "# one home for the gate list and a generator reaching in here for it would recreate the very\n"
 "# copy it exists to remove. `render-standard.py --blocks` fills every one;", 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("blocks declared")
