import datetime, pathlib
p = pathlib.Path("LOG.md")
entries = [
 ("add", "c-gate-count-restated-in-prose opened, HIGH. The count has one true home in .github/gates.yaml and is hand-copied into README, CLAUDE.md, ARCHITECTURE and current_state. It went 9 -> 11 -> 12 -> 13 today and every move falsified four or five sentences; the last round also moved the SKIP count 2 -> 3. Same shape as the stage-table concern settled this morning, and the claim surface cannot catch it because it checks paths not values"),
 ("fix", "current_state was STALE IN ITS OPENING TWO LINES at session close: 'Stage `build` ... version 0.8.1', written above a repository that had been public for two hours and a plugin eleven versions further on. The claims block passed GREEN the whole time. That is its DECLARED limit behaving exactly as specified, and it is why the paragraph carries the standing-example note"),
 ("fix", "ARCHITECTURE brought current — it is declared must-be-current, and the shape changed today. Its scripts inventory listed neither rite_copy.py nor the three new tests, its check count said 61/57-of-64, and its skip sentence still said two gates when three now skip on a runner"),
 ("note", "A TOOLING HAZARD THAT COST A REPAIR: `sed -i 's|...|...|'` with `|` used as BOTH the delimiter and a regex alternation clobbered hooks/rite.sh line 13 to the literal 'X'. Caught by reading the file afterwards, not by sed, which reported nothing. Same family as the heredoc truncation of 2026-09-09 — a shell edit that succeeds loudly and damages quietly"),
 ("note", "SESSION SHAPE, because the ordering was again the story and again unplanned. Reading the handoff turned up that its pre-publish check rested on a false premise; verifying that instead of performing it found two more defects; publishing exposed a third; porting the copiers found a fourth in its own first implementation; and wiring the port found a fifth by testing rather than reading. Five defects, each one surfaced by acting on the previous finding"),
 ("note", "THE RECURRING THEME across all five: things that READ AS COVERED and were not. A rule declared and enforced by nothing; a shim tested by CI but unreachable in production; a test whose artifact path could never match; an attributor contaminated by the session measuring it; and a checker whose advice fixed nothing because copier and checker judged staleness differently. A visible gap is cheap. A green light over a gap is what this project exists to attack"),
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
