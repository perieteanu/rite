import pathlib, sys
edits = [
# README: the whole hand-maintained sentence becomes a generated block
("README.md",
 """Thirteen gates run on every push, across Linux, macOS and Windows. Three of them cannot run on
a CI runner — the YAML parser's differential test needs PyYAML as an oracle, the installed-copy
test needs an installed plugin, and the mirror-port parity test needs the original script Rite
ported from — so the runner reports **`10 of 13 gates ran`** and names the three it skipped
rather than showing an unqualified green.
""",
 """<!-- rite:generated gate-counts -->
<!-- /rite:generated -->
"""),
# ARCHITECTURE: a generated table replaces the hand-written skip sentence
("docs/ARCHITECTURE.md",
 """**A skip is never folded into green.** Three gates cannot run on a runner — `test-riteyaml.py`
(PyYAML is its oracle and CI does not install it), `test-installed-current.py` (a runner has no
installed plugin) and `test-mirror-port-parity.py` (a runner has no copy of the script Rite
ported from) — so the runner prints `10 of 13 gates ran` and names what was not enforced.
""",
 """**A skip is never folded into green.** The runner names what it could not enforce, rather than
showing an unqualified green:

<!-- rite:generated gate-list -->
<!-- /rite:generated -->

"""),
# CLAUDE.md: DELETE the number, point at the source
("CLAUDE.md",
 "- **CI runs THIRTEEN gates, but only ten of them on a runner.** `.github/workflows/gates.yml`\n",
 "- **CI runs the gates declared in `.github/gates.yaml`, and not all of them on a runner.**\n"
 "  The count is deliberately NOT repeated here — it went 9 to 13 in one day and falsified four\n"
 "  documents each time (`c-gate-count-restated-in-prose`). Read the file.\n"
 "  `.github/workflows/gates.yml`\n"),
# ROADMAP current_state: DELETE the numbers
("docs/ROADMAP.yaml",
 "  THIRTEEN GATES RUN, AND CI NOW RUNS THEM: standard, protocol, generated blocks, riteyaml\n"
 "  differential, mirror-port parity, stage-table guard, copy attribution, hook output",
 "  THE GATES RUN, AND CI RUNS THEM. The list and the count live in .github/gates.yaml and are\n"
 "  NOT repeated here: hook output"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}\n  {old[:70]}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"{rel} updated")
