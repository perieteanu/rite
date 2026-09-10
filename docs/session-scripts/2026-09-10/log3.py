import datetime, pathlib
p = pathlib.Path("LOG.md")
entries = [
 ("add", "The copiers are wired in. /rite:end gains a copy step, SessionEnd calls all three IN-PROCESS (the subprocess to ~/.claude/scripts/claude-mirror-memory.py is gone, and with it the dependency on a file only this machine has), and a PostToolUse hook refreshes the mirror when a memory file is written"),
 ("fix", "THE GLOBAL claude-mirror-memory HOOKS ARE RETIRED — three entries removed from ~/.claude/settings.json (SessionStart startup, SessionStart resume, PostToolUse). settings.json backed up first; everything outside the `hooks` key verified byte-identical, and preflight's two SessionStart entries survive untouched"),
 ("note", "Retirement is lossless and each half was checked rather than assumed. The SessionStart --check half is replaced by mirror_not_stale inside rite's own verdict, which is strictly more actionable — it names WHEN the memory changed and what to run, where the old line said STALE. The PostToolUse half is replaced by rite's own, gated on the path so it costs nothing on a normal edit"),
 ("fix", "A DEFECT FOUND BY TESTING THE HOOK RATHER THAN READING IT: the copier skipped rewriting whenever CONTENT matched, while the checker judged staleness from the STAMP. So a mirror with a stale stamp and correct content was YELLOW forever and the checker's own advice — 'run --memory' — did nothing. Two implementations of one predicate, drifting inside the hour they both existed"),
 ("note", "Fixed by sharing one predicate, mirror_is_stale, between checker and copier — the same move as uncopied_plans. The copier now reports `restamped` as a distinct outcome from `wrote`, because refreshing a stamp over unchanged content is a different fact and collapsing them would hide it"),
 ("note", "PostToolUse was documented as DELIBERATELY ABSENT, on two grounds: it would call a script only this machine has, and it would double-fire against settings.json. Both became false in the same commit — the port exists and the settings entry is retired — so the paragraph is rewritten rather than the hook being added against a standing objection"),
 ("note", "Measured before adding it: a full mirror refresh is ~66ms including Python startup. PostToolUse fires on every Write and Edit, so the hook exits early unless the written path is under a memory dir. A hook that makes editing feel slow is a hook the user removes"),
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
