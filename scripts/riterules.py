#!/usr/bin/env python3
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
import fnmatch
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import riteyaml  # noqa: E402


def git_show(root: Path, rel: str) -> str | None:
    """The committed version of a file at HEAD, or None if unavailable."""
    try:
        # encoding is LOAD-BEARING here, not hygiene. git emits the blob's bytes; text=True
        # alone decodes them with the locale, so on Windows a UTF-8 document comes back as
        # cp1252 mojibake. It still PARSES — mojibake is valid YAML text — and every scalar
        # then differs from the same scalar read with encoding="utf-8", so milestones_append_only
        # reported an existing milestone as CHANGED on a file that had only been appended to.
        # RED on windows, GREEN on ubuntu and macOS, from one missing argument. Found by CI on
        # 2026-09-10. See portability `process_output_declares_encoding`.
        out = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{rel}"],
                             capture_output=True, text=True, timeout=10,
                             encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def zone_of(root: Path, rel: str, key: str):
    """(committed_value, current_value) for one top-level key. None when unavailable.

    Line-diffing a MIXED file is wrong: ROADMAP has three zones with three different
    disciplines, and deleting from the rewrite-only zone is not merely legal but REQUIRED
    when closing an item. A whole-file diff cannot tell that from rewriting a milestone.
    """
    old_text = git_show(root, rel)
    if old_text is None:
        return None
    try:
        old = riteyaml.load(old_text, f"HEAD:{rel}") or {}
        new = riteyaml.load((root / rel).read_text(encoding="utf-8"), rel) or {}
    except (riteyaml.RiteYamlError, OSError):
        return None
    return old.get(key), new.get(key)


def git_removed_lines(root: Path, rel: str) -> int | None:
    """Lines deleted from a tracked file relative to HEAD. None when unavailable."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "diff", "-U0", "HEAD", "--", rel],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return sum(1 for ln in out.stdout.splitlines() if ln.startswith("-") and not ln.startswith("---"))


# ── every YAML file a project carries, not only its declared artifacts ───────
# WHY THIS IS HERE and not in the checker: the PostToolUse watcher asks the same question the
# instant a file is written, and the checker asks it at session start. Two copies of "is this
# file readable, and is it inside the subset?" would be free to disagree — the drift this project
# attacks everywhere else, self-inflicted. One predicate, two consumers, like the append-only
# and future-timestamp rules above.

def git_known_files(root: Path) -> set[str] | None:
    """Every path git knows about: tracked, plus untracked and not ignored. None if not a repo.

    An IGNORED file is deliberately absent from this set. A project that has told git not to
    publish a file has said it is not part of what the project claims about itself, and Rite has
    no standing to grade it. Where there is no repository there is no such statement, so the
    filesystem is used and ignored files do not exist as a category.
    """
    if not (root / ".git").is_dir():
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z",
             "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return {p for p in out.stdout.split("\0") if p}


def _glob_set(root: Path, patterns: list[str]) -> dict[str, None]:
    """Case-exact matches for a list of globs, in declaration order, de-duplicated.

    Path.glob alone matches case-insensitively on macOS and Windows, so docs/roadmap.yaml would
    satisfy docs/*.yaml there and not on Linux — the same repo, two verdicts. Every hit is
    re-verified through ritefs.exists_exactly, which is the one implementation of that rule.
    """
    out: dict[str, None] = {}
    for pattern in patterns:
        try:
            found = sorted(root.glob(pattern))
        except (ValueError, OSError):
            continue  # a malformed glob is the project's declaration, not a crash of ours
        for p in found:
            if p.is_file() and ritefs.exists_exactly(p):
                out[p.relative_to(root).as_posix()] = None
    return out


def project_yaml_globs(spec: dict, marker: dict | None) -> tuple[list[str], list[str], int]:
    """(include, exclude, how many globs the project declared itself).

    The default comes from the spec and is expanded over every documentation directory name the
    standard knows, including the superseded ones — 11 projects still use docs-yaml/ and
    migration is opt-in, so checking only the canonical name would check nothing on those.
    """
    cf = (spec.get("yaml_subset") or {}).get("checked_files") or {}
    local = (spec.get("local") or {}).get("docs_dir") or {}
    dirs = [local.get("default") or "docs", *(local.get("alternatives") or [])]
    include = [str(pattern).replace("{docs_dir}", d)
               for pattern in cf.get("include_default") or []
               for d in dirs]
    declared = (marker or {}).get("yaml_check") or {}
    extra = [str(x) for x in (declared.get("include") or [])]
    exclude = [str(x) for x in (declared.get("exclude") or [])]
    return include + extra, exclude, len(extra)


def project_yaml_files(root: Path, spec: dict,
                       marker: dict | None) -> tuple[list[str], dict]:
    """The YAML files in scope, and what narrowed the scope.

    The second value is reported rather than kept quiet: a declared include or exclude that
    nothing states is a silent opt-out, which is the rule threshold overrides already follow.
    """
    include, exclude, declared_globs = project_yaml_globs(spec, marker)
    candidates = _glob_set(root, include)
    known = git_known_files(root)
    ignored = 0
    if known is not None:
        kept = {}
        for rel in candidates:
            if rel in known:
                kept[rel] = None
            else:
                ignored += 1
        candidates = kept
    removed = set(_glob_set(root, exclude))
    files = [rel for rel in candidates if rel not in removed]
    return sorted(files), {
        "declared_globs": declared_globs,
        "excluded": len(candidates) - len(files),
        "ignored_by_git": ignored,
    }


# ── what the project last RECORDED as changed ────────────────────────────────
# Freshness asks whether a document is older than the thing it describes, so this is the measure
# every freshness verdict rests on. It used to be "the newest mtime on disk", which was wrong in
# both directions: a .gitignore or an ignored PDF made a documents-only project look like it had
# source, and `touch` could silence a genuinely stale document. c-source-is-filesystem-mtime.
#
# The definition is DECLARED in spec/project-standard.yaml under `source_definition`; this code
# reads it rather than carrying its own copy.

class SourceActivity(NamedTuple):
    """What the project last recorded as changed, and how much that answer is worth.

    `date` is None whenever the answer is unknowable, and `reason` then says which of the three
    ways it is unknowable — shallow clone, no commits yet, or genuinely no source. Those are
    different facts about different projects and must not share one sentence.
    """

    date: dt.date | None
    reason: str
    dirty: bool
    mode: str


def _source_exclusions(spec: dict, marker: dict | None) -> list[str]:
    """Every path that is not source, from the spec plus whatever the project declares."""
    sd = spec.get("source_definition") or {}
    local = (spec.get("local") or {}).get("docs_dir") or {}
    dirs = [local.get("default") or "docs", *(local.get("alternatives") or [])]
    out: list[str] = []
    for raw in sd.get("excluded_paths") or []:
        pattern = str(raw)
        if "{docs_dir}" in pattern:
            out.extend(pattern.replace("{docs_dir}", d) for d in dirs)
        else:
            out.append(pattern)
    out.extend(str(p) for p in (sd.get("operational_not_source") or {}).get("paths") or [])
    out.extend(str(p) for p in (marker or {}).get("source_exclude") or [])
    return out


def _pathspecs(exclusions: list[str]) -> list[str]:
    """git exclude pathspecs. `glob` magic only where the pattern actually needs it."""
    specs = []
    for e in exclusions:
        specs.append(f":(exclude,glob){e}" if "*" in e else f":(exclude){e}")
    return specs


def _git(root: Path, args: list[str]) -> subprocess.CompletedProcess | None:
    """git, or None when it could not be run at all. encoding is load-bearing — see git_show."""
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                              timeout=15, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None


def _git_source_activity(root: Path, exclusions: list[str]) -> SourceActivity | None:
    """The git answer, or None when git itself could not be asked (then mtime is the fallback)."""
    shallow = _git(root, ["rev-parse", "--is-shallow-repository"])
    if shallow is None:
        return None
    if shallow.returncode == 0 and shallow.stdout.strip() == "true":
        return SourceActivity(
            None,
            "shallow clone — every file's last commit is the clone's, so a date here would "
            "describe how the repository was fetched rather than when the project changed",
            False, "git")
    specs = _pathspecs(exclusions)
    log = _git(root, ["log", "-1", "--format=%cs", "--", ".", *specs])
    if log is None:
        return None
    if log.returncode != 0:
        # Exit 128, "does not have any commits yet". NOT the same fact as documents-only: a project
        # scaffolded by /rite:init and checked before its first commit lands here.
        return SourceActivity(
            None, "no commits yet — nothing has been recorded to measure a document against",
            False, "git")
    stamp = log.stdout.strip()
    if not stamp:
        return SourceActivity(
            None, "documents-only project — no source has ever been committed", False, "git")
    try:
        when = dt.date.fromisoformat(stamp)
    except ValueError:
        return None
    status = _git(root, ["status", "--porcelain", "--", ".", *specs])
    dirty = bool(status and status.returncode == 0 and status.stdout.strip())
    return SourceActivity(when, "", dirty, "git")


def _excluded(rel: str, exclusions: list[str]) -> bool:
    name = rel.rsplit("/", 1)[-1]
    for e in exclusions:
        if e.endswith("/"):
            bare = e.rstrip("/").removeprefix("**/")
            if rel == bare or rel.startswith(f"{bare}/") or f"/{bare}/" in f"/{rel}":
                return True
        elif "*" in e:
            if fnmatch.fnmatchcase(rel, e) or fnmatch.fnmatchcase(name, e):
                return True
        elif rel == e or name == e:
            return True
    return False


def _mtime_source_activity(root: Path, exclusions: list[str]) -> SourceActivity:
    """The filesystem answer, for a project with no repository to ask.

    Six of ten sampled projects on this machine are not repositories, including the non-code ones
    d-noncode-first-class exists to serve, so this is a real path rather than a safety net. Its
    limitation is declared rather than hidden: after a fresh checkout every mtime is checkout time,
    and nothing here can tell that from work.
    """
    newest: dt.date | None = None
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith(".git/") or _excluded(rel, exclusions):
            continue
        try:
            when = dt.date.fromtimestamp(p.stat().st_mtime)
        except OSError:
            continue
        if newest is None or when > newest:
            newest = when
    if newest is None:
        return SourceActivity(
            None, "documents-only project — no source to measure against", False, "mtime")
    return SourceActivity(newest, "", False, "mtime")


def newest_source_date(root: Path, spec: dict, marker: dict | None = None) -> SourceActivity:
    """When the project last recorded a change to something a document could describe."""
    exclusions = _source_exclusions(spec, marker)
    if (root / ".git").is_dir():
        # A git WORKTREE carries .git as a file, not a directory, so it takes the mtime path. The
        # finding names the mode, which is the honest half of that limitation.
        activity = _git_source_activity(root, exclusions)
        if activity is not None:
            return activity
    return _mtime_source_activity(root, exclusions)


def yaml_verdict(path: Path, rel: str) -> tuple[str, str, str] | None:
    """(kind, construct, message) when a YAML file cannot be read as declared, else None.

    `kind` is riteyaml's: "invalid" for text that is not YAML, "unsupported" for valid YAML
    outside the declared subset. The caller turns that into a verdict; deciding it here would put
    the severity in two places.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ("invalid", "not_utf8",
                "not valid UTF-8 — YAML must be UTF-8, UTF-16 or UTF-32, and every file Rite "
                "reads or writes declares UTF-8")
    except OSError:
        return None  # unreadable for a reason that is not about its content
    try:
        riteyaml.load(text, rel)
    except riteyaml.RiteYamlError as e:
        return e.kind, e.construct, f"{e.reason} (line {e.lineno})"
    return None


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
LOG_TS = re.compile(r"^(\d{2})-(\d{2})-(\d{4})\s+(\d{2}):(\d{2})(?::(\d{2}))?")

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
