import datetime, pathlib
p = pathlib.Path("LOG.md")
entries = [
 ("fix", "c-gate-count-restated-in-prose SETTLED hours after opening — d-one-home-for-the-gate-count. Same shape as the stage table and the same two-part answer: GENERATE where the number earns its place, DELETE where it does not. README and ARCHITECTURE carry rite:generated blocks fed from .github/gates.yaml; CLAUDE.md's and current_state's copies are gone and point at the file"),
 ("note", "The split is by AUDIENCE, not by convenience. A stranger reading the README is deciding whether to care and a count helps them. An agent reading CLAUDE.md and a session reading current_state need to know WHERE the gates are declared, which stays true when the number does not"),
 ("add", "generated_blocks gains `source_file`, and this is the general fix rather than a special case: every block until today generated from the standard alone, which would have forced the gate list INTO spec/project-standard.yaml to be reachable — recreating the copy the block exists to remove. Blocks are now source-agnostic"),
 ("add", "gates.yaml gains `skip_short` beside `skip_means` — the same fact in one clause, for prose. The skipped COUNT needs no second source: a gate that declares it is a gate that can skip, so both numbers and every reason come from one file"),
 ("note", "PROVED BY ADDING A FICTIONAL 14TH GATE to the authority. Both documents were flagged stale, the count moved 13 -> 14 and 3 -> 4, and '10 of 13' became '10 of 14' — no document edited by hand. Restored byte-identical afterwards, from a file copy, never git checkout"),
]
lines = []
for kind, text in entries:
    now = datetime.datetime.now()
    dow = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][now.weekday()]
    lines.append(f"{now.strftime('%d-%m-%Y %H:%M:%S')} | {dow} | rite | [{kind}] {text}")
before = len(p.read_bytes())
with p.open("a", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print(f"LOG.md: {before} -> {len(p.read_bytes())}, +{len(lines)}")
