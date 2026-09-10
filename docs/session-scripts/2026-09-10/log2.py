import datetime, pathlib
p = pathlib.Path("LOG.md")
entries = [
 ("add", "scripts/rite_copy.py — ONE copier, THREE sources. port-mirror-memory's own note set the shape ('Plans are the identical problem with a different source dir. One tool, not two') and session-script copy joined them: the scratchpad is in /tmp and does not survive a reboot, so the scripts that performed a commit's edits are lost unless copied"),
 ("fix", "c-plan-attribution SETTLED after three days as 'the only genuinely hard part'. It was never hard: session transcripts are filed under the project slug and record a plan as a TOOL INPUT — a Write naming it as file_path, or an ExitPlanMode as planFilePath. Exact, retroactive, no mtime correlation and no content inspection"),
 ("fix", "THE FIRST ATTRIBUTOR WAS WRONG AND NOTHING ABOUT IT LOOKED WRONG. Matching the plan's path as a string mis-attributed FIVE of thirteen plans. The contamination was self-inflicted: this session ran `ls ~/.claude/plans/`, so rite's own transcript came to mention every plan on the machine and the naive index handed rite half of hwprivacy's work. The act of measuring changed what was measured"),
 ("note", "It was caught only by DISAGREEMENT — the new numbers contradicted a shell measurement taken twenty minutes earlier. That is the argument for writing a measurement down before trusting the tool that replaces it. scripts/test-copy-attribution.py now encodes the distinction on synthetic fixtures, and was proved to catch the exact bug by reintroducing it"),
 ("fix", "Dedupe is keyed on CONTENT, not source filename, and that is a property of the harness rather than a preference: ~/.claude/plans/<name>.md is REUSED. calm-tinkering-kahan.md held the publishing plan this morning and the copier plan this afternoon. Keyed on filename the second would have been skipped as 'already copied' and lost — the quiet kind of data loss, where the tool reports success"),
 ("fix", "c-pattern-paths-are-matched-literally settled, and it was a PREREQUISITE not a neighbour: until an artifact could declare a glob, both plan_copy tests reported 'not present' with two real copies on disk. Artifacts now declare path_pattern for presence and canonical_name_pattern for shape"),
 ("note", "The second key came out of building the first. filename_matches_canonical initially held the PLAN regex inside the checker — a hardcoded value with no human-visible home, and silently wrong for the very next artifact to declare the rule. script_copy went YELLOW with all 20 instances 'wrong' the moment it was declared, which is how it surfaced"),
 ("add", "THREE declared tests implemented — filename_matches_canonical, source_plans_all_copied, mirror_not_stale. Coverage 57 of 64 -> 61 of 66. All three proved to FAIL before being trusted: a non-canonical filename, a deleted copy, and a sync stamp wound back. Two of them were UNREACHABLE rather than merely unwritten"),
 ("add", "script_copy is the FOURTEENTH artifact, added through the process the freeze exists to force — a DECISIONS entry — rather than around it. Grouped by date, unlike plan_copy which is flat: one session produced twenty helper scripts and a few such sessions would bury docs/ under machinery"),
 ("note", "The memory mirror is a PORT, not a rewrite, and the test says so: regenerated output differs from the global hook's only in the clock. The global ~/.claude hook is deliberately left running beside it — two writers producing identical bytes is safe, swapping them mid-port is not"),
 ("fix", "claude_home_slug_derivation was severity: open, 'not yet solved', deferred to exactly this work. Resolved by not needing the hard direction: root -> slug is exact and governs every write; slug -> root is lossy and may only name a project in a report. A wrong name in a report is cosmetic; a wrong directory to write into is data loss"),
 ("note", "watcher-plan-copy-on-create loses its premise. It existed to close c-plan-attribution because that problem 'is only hard retroactively'. Retroactive attribution now works, so the watcher buys latency and nothing else. Recorded on the item rather than left to be rediscovered"),
 ("note", "Backfill wrote into rite ONLY — 4 plans copied, 9 reported as belonging elsewhere and left alone. Verified by git status in hwprivacy, tattvas, claude-persistent and plumbing rather than by reading the tool's own summary: 0 uncommitted in hwprivacy, and tattvas' single modified file predates today by two days"),
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
