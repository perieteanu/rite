import pathlib, sys
p = pathlib.Path("skills/end/SKILL.md")
t = p.read_text(encoding="utf-8")
old = """2. **Bring the docs back to true.** For each, check the claim against the filesystem or the
   host, never against another document:
"""
new = """2. **Bring the docs back to true**, then **say how much you had to correct** — one line, into
   the log. That line is the only verification `/rite:update` has: if checkpoints kept the docs
   true this step finds little, and if it rewrites `current_state` they lapsed. Report the
   magnitude; never score it. Any pass/fail threshold would be a guessed number.

   For each, check the claim against the filesystem or the host, never against another document:
"""
if t.count(old) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("end skill updated")
