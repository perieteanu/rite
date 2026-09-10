import pathlib, sys
src = pathlib.Path("scripts/rite-check.py")
t = src.read_text(encoding="utf-8")

start = t.index("def git_show(root: Path, rel: str) -> str | None:")
end = t.index("# ── rules ─────────────────────────────────────────────────────────────────")
block = t[start:end].rstrip() + "\n"

header = '''#!/usr/bin/env python3
"""riterules — predicates shared by the checker and the PostToolUse watcher.

ONE IMPLEMENTATION, TWO CONSUMERS, and the reason is this project's most repeated lesson.
scripts/rite-check.py asks "was this append-only file rewritten?" at session start;
scripts/rite_watch.py asks the same question the instant the write happens. Two copies of that
predicate would be free to disagree, which is the drift the mirror and preflight parity gates
exist to catch — and it would be self-inflicted rather than inherited.

Extracted from rite-check.py on 2026-09-10, unchanged. The comments carried over with them are
worth keeping: the encoding argument in git_show is load-bearing, and CI proved it.

Stdlib only, like everything else here.
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import riteyaml  # noqa: E402


'''

footer = '''

# ── LOG timestamps ───────────────────────────────────────────────────────────
# c-log-timestamps-must-be-machine-read, open since 2026-09-08 with nowhere to run.
#
# THE FAILURE IT ENCODES IS REAL AND THIS PROJECT'S OWN: on 2026-09-07 the clock was read once
# at 22:11 and roughly thirty further entries carried extrapolated times, some AHEAD of real
# time, discovered only when the clock was re-read at 00:02 against entries claiming 00:13.
# CONVENTIONS already forbade it — "the machine clock. Never invent, round, or approximate" —
# and the rule failed exactly the way this project says rules fail: nothing checked it.
#
# A timestamp in the FUTURE is the one form of invention that is provable after the fact. An
# invented time in the past is indistinguishable from a real one, which is why the check is
# narrow and why it is worth having anyway: extrapolation overshoots, and this one did.
LOG_TS = re.compile(r"^(\\d{2})-(\\d{2})-(\\d{4})\\s+(\\d{2}):(\\d{2})(?::(\\d{2}))?")

# A minute of slack. The entry is written before the file lands, clocks are not monotonic across
# a filesystem, and a check that fires on a one-second skew is a check that gets switched off.
FUTURE_TOLERANCE = dt.timedelta(minutes=1)


def log_future_timestamps(text: str, now: dt.datetime | None = None) -> list[str]:
    """Entries dated later than `now`. Empty means every timestamp is plausibly machine-read.

    Day-first (DD-MM-YYYY), which is the declared local convention — see the `local` layer in
    the standard. A date that cannot be parsed is NOT reported here: entries_parse owns that,
    and two rules reporting one defect is noise.
    """
    when = now or dt.datetime.now()
    limit = when + FUTURE_TOLERANCE
    out: list[str] = []
    for line in text.splitlines():
        m = LOG_TS.match(line.strip())
        if not m:
            continue
        d, mo, y, h, mi = (int(x) for x in m.groups()[:5])
        sec = int(m.group(6) or 0)
        try:
            ts = dt.datetime(y, mo, d, h, mi, sec)
        except ValueError:
            continue
        if ts > limit:
            out.append(line.strip()[:80])
    return out
'''

pathlib.Path("scripts/riterules.py").write_text(header + block + footer, encoding="utf-8", newline="\n")
print(f"riterules.py written: {len(pathlib.Path('scripts/riterules.py').read_bytes())} bytes")

# rite-check now imports them instead of defining them
t = t[:start] + t[end:]
t = t.replace("import riteyaml  # noqa: E402\nimport ritefs  # noqa: E402",
              "import riteyaml  # noqa: E402\nimport ritefs  # noqa: E402\nimport riterules  # noqa: E402\n"
              "from riterules import git_removed_lines, git_show, zone_of  # noqa: E402,F401", 1)
src.write_text(t, encoding="utf-8", newline="\n")
print("rite-check.py now imports them")
