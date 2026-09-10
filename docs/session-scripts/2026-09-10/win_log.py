import datetime, pathlib
p = pathlib.Path("LOG.md")
entries = [
 ("fix", "c-rite-ps1-unreachable-in-production SETTLED — d-git-bash-required-on-windows. Answered WITHOUT a Windows machine, from the vendor docs, after the shipped binary proved inconclusive: its 'hooks.*win32' hits were minified JS spanning long lines, not hook-platform code. That is the authority order the memory rule already prescribes, applied and vindicated"),
 ("note", "THE HOOKS REFERENCE SAYS OUTRIGHT that a hook entry supports no per-platform conditional. So one command string must serve every platform and none does: `bash X` fails under PowerShell, a bare .sh path fails under PowerShell, a bare .ps1 path fails under sh. Exec form skips the shell and would solve it, except it needs one executable name resolving everywhere — the exact problem the shim exists for, and THIS machine has no bare `python` on PATH"),
 ("fix", "Settled by NARROWING THE CLAIM rather than widening the code. Git Bash is required on Windows; every hooks.json entry now declares `shell: bash`, which changes nothing where Git Bash exists and removes a silent fallback to a PowerShell that could only fail at our command string. The spec's fourth coverage row now says hooks do not run there, and rite.ps1 is documented as a manual entry point"),
 ("note", "The false row cost nothing to write and would have cost a Windows user their entire install, silently. It described the design INTENT and nothing ever implemented it — while CI passed the .ps1 all along by invoking it directly. A green test over a code path production cannot reach"),
 ("note", "The idea NOT taken, recorded so it is not re-proposed as new: two hook entries with explicit `shell:` fields. The docs do not specify what a hook declaring an UNAVAILABLE shell does — skip, error or fall back — and building on undocumented behaviour is guessing, which is the rule riteyaml and the plan attributor both already live by"),
 ("add", "Hook entries also accept `if`, `args`, `async`, `once` and `shell` — none of which Rite knew about. Added to the locked findings so the next session does not re-derive the hook schema"),
 ("note", "RULING on the lighter mid-session command, to be built: it is /rite:update. It takes /end's steps 1, 2, 3, 6 and 7 — distil, bring docs true, close finished items, copy, check — and explicitly NOT 4 (handoff) or 5 (memory), because those are what make an ending. Costin asked whether /end can verify it ran by comparing content: yes, and the evidence is the correction /end has to make. If /rite:update kept the docs true, /end's step 2 finds nothing. No stamp file, no fifteenth artifact"),
 ("note", "That verification must be REPORTED, NOT GRADED. /end always has some correction to make for the work since the last checkpoint, so any pass/fail threshold would be a guessed number — the exact mistake already open as c-freshness-thresholds-are-guesses. Record the magnitude in LOG and let the pattern show over weeks"),
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
