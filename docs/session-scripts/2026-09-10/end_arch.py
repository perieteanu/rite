import pathlib, sys
p = pathlib.Path("docs/ARCHITECTURE.md")
t = p.read_text(encoding="utf-8")
edits = [
 ("""  rite-check.py      THE CHECKER. Reads spec/project-standard.yaml and runs the completion
                     tests. 61 checks on this project; 57 of 64 declared tests implemented.
""",
  """  rite-check.py      THE CHECKER. Reads spec/project-standard.yaml and runs the completion
                     tests. 62 checks on this project; 61 of 66 declared tests implemented.
  rite_copy.py       THE COPIER. Brings in what Claude writes OUTSIDE the project: the memory
                     mirror (free_replace, one file), plan copies and session scratchpad
                     scripts (write_once, many). Attribution is AUTHORSHIP — a Write or
                     ExitPlanMode naming the file in a transcript — never mention. Refuses
                     rather than guesses. Also the PostToolUse entry point, via --hook.
  test-copy-attribution.py  Synthetic-fixture test that writing and mentioning stay distinct.
                     Encodes a defect that shipped for twenty minutes.
  test-mirror-port-parity.py  The port still renders identically to the script it replaced.
                     TEMPORARY: delete it when the fallback is retired.
  test-stage-table-guard.py  No document restates the stage mapping outside a generated block.
"""),
 ("""**A skip is never folded into green.** Two gates cannot run on a runner — `test-riteyaml.py`
(PyYAML is its oracle and CI does not install it) and `test-installed-current.py` (a runner has
no installed plugin) — so the runner prints `10 of 13 gates ran` and names what was not enforced.
""",
  """**A skip is never folded into green.** Three gates cannot run on a runner — `test-riteyaml.py`
(PyYAML is its oracle and CI does not install it), `test-installed-current.py` (a runner has no
installed plugin) and `test-mirror-port-parity.py` (a runner has no copy of the script Rite
ported from) — so the runner prints `10 of 13 gates ran` and names what was not enforced.
"""),
]
for old, new in edits:
    if t.count(old) != 1:
        sys.exit(f"ABORT: matched {t.count(old)}\n{old[:80]}")
    t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("ARCHITECTURE updated")
