import datetime, pathlib
p = pathlib.Path("LOG.md")
entries = [
 ("fix", "~/.claude/commands/mirror-memory.md corrected — three claims had gone false when the global hook was retired: the description and body both said the automatic write is claude-mirror-memory's PostToolUse hook (it is rite's now), and the script line said 'engine shared with the hook' (it is not). The SCRIPT PATH is unchanged on purpose: Costin keeps the original as a fallback while rite is on trial"),
 ("add", "scripts/test-mirror-port-parity.py — a gate for the fact that two implementations of one output are now alive at once. 'They agree' had been verified twice by hand and by nothing else, which is exactly the kind of claim this project refuses to accept from anyone else"),
 ("note", "It compares the two GENERATORS rather than their files, so it writes nothing and needs no temp project: both engines expose a pure function from (slug, memory files) to text. The Last sync line is excluded — it is a clock, and no generated file here carries one"),
 ("note", "TEMPORARY BY CONSTRUCTION, and the gate says so in its own skip_means: when Costin retires the fallback it will skip forever, and at that point it must be DELETED along with the parity sentence in mirror-memory.md. A gate that can no longer fail is not a gate"),
 ("note", "Proved both ways before trusting it. Drifting the port's separator (· to —) produced a FAIL with a readable diff; pointing LEGACY at a nonexistent path produced exit 2 and a skip that explains itself. The first probe failed for a harness reason — the copy sat outside scripts/ so its imports broke — which is worth recording because the exit code looked like a real failure and was not"),
 ("fix", "Gate count 12 -> 13, and the SKIP count 2 -> 3, which falsified five sentences across README, CLAUDE.md, ARCHITECTURE and ROADMAP for the third time today. The README still opened with 'Nine gates run on every push' under a corrected total"),
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
