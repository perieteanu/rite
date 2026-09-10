#!/usr/bin/env python3
"""rite-check — run the project standard's completion tests against a project.

Reads spec/project-standard.yaml (the authority) and executes the tests each artifact
declares. Stdlib only; YAML via scripts/riteyaml.py.

    python scripts/rite-check.py [PROJECT_DIR] [--force] [--exclude-scope=SCOPE]

--exclude-scope=SCOPE skips every test the standard declares with that `scope:`, reporting
each as NA naming the exclusion rather than dropping it. CI passes --exclude-scope=session,
because a session-scoped test asks whether the session running RIGHT NOW has closed — true
only after /end, so it is RED by design for the whole working life of a session and belongs
at SessionStart, not in a pipeline. It is a caller's statement about WHERE a check runs, and
deliberately not settable in .rite.yaml: a project must not switch off a scope for itself.

PARTICIPATION IS OPT-IN. Without a .rite.yaml marker the project is not checked and nothing
is printed — see `participation` in the spec. Rite is silent where it was not invited.

VERDICTS follow the spec's level_to_severity mapping, inherited from claude-preflight:
  exists / integrity  -> RED     (missing, or actively wrong)
  populated / fresh   -> YELLOW  (present but thin, or true once and not now)
Exit 1 on any RED. YELLOW alone exits 0, so the gate stays credible; `fail_on` overrides.

A DECLARED RULE THIS CHECKER DOES NOT IMPLEMENT REPORTS **NA**, NEVER SILENCE.
That is the point: the report states its own coverage, so the gap between what the standard
claims and what it can actually verify is visible rather than flattering. A check that
vanishes and a check that passed must never look alike.
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
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

SPEC_PATH = HERE.parent / "spec" / "project-standard.yaml"

RED, YELLOW, GREEN, NA = "RED", "YELLOW", "GREEN", "NA"
LEVEL_SEVERITY = {"exists": RED, "integrity": RED, "populated": YELLOW, "fresh": YELLOW}


class Finding:
    # `deferred_to` carries the stage an artifact is waiting for, and exists only so the report
    # can COLLAPSE those lines instead of printing one per check. It never affects a verdict or
    # a count — see report().
    __slots__ = ("severity", "side", "level", "rule", "path", "message", "deferred_to")

    def __init__(self, severity, side, level, rule, path, message, deferred_to=None):
        self.severity, self.side, self.level = severity, side, level
        self.rule, self.path, self.message = rule, path, message
        self.deferred_to = deferred_to


class Ctx:
    """Everything a rule needs to know, gathered once."""

    def __init__(self, root: Path, spec: dict, excluded_scopes: set[str] | None = None):
        self.root, self.spec = root, spec
        # Caller-level, never project-level: a project must not be able to switch off a scope
        # for itself in .rite.yaml. Excluding is a statement about where the check is RUN.
        self.excluded_scopes = excluded_scopes or set()
        self.unreadable: dict[str, str] = {}
        self.marker_error: str | None = None
        self.marker = self._load_marker()
        self.is_git = (root / ".git").is_dir()
        self.today = dt.date.today()
        # The project's own declared stage, and its position in the vocabulary. None when the
        # marker declares none — see `no_stage_declared` in the spec: absence is not a claim,
        # so the thresholds do not apply and tier-based requirement stands.
        self.stage = (self.marker or {}).get("stage")
        order = spec.get("stage_vocabulary", {}).get("values", [])
        self.stage_index = order.index(self.stage) if self.stage in order else None
        self.thresholds = (self.marker or {}).get("thresholds") or {}
        self.disabled = set((self.marker or {}).get("disabled_checks") or [])
        self.fail_on = (self.marker or {}).get("fail_on", "red")

    def not_yet_required(self, art: dict) -> str | None:
        """Why this artifact is not required at the project's declared stage, or None.

        Returns the reason so the caller can REPORT it. An artifact that is simply not due yet
        must not look like one that passed, and must not look like one that failed either.
        """
        want = art.get("required_from_stage")
        if want is None or self.stage_index is None:
            # No declaration, or no declared stage. Both fall back to tier, which the caller
            # applies. `no_stage_declared` in the spec is the reasoning for the second case.
            return None
        order = self.spec.get("stage_vocabulary", {}).get("values", [])
        try:
            if self.stage_index >= order.index(want):
                return None
        except ValueError:
            return None
        return f"not required before stage {want} — this project declares {self.stage}"

    def _load_marker(self):
        p = self.root / ".rite.yaml"
        if not p.exists():
            return None
        try:
            return riteyaml.load(p.read_text(encoding="utf-8"), str(p)) or {}
        except riteyaml.RiteYamlError as e:
            # An unreadable marker silently dropped every threshold and override. Record it:
            # running on defaults while the project believes its overrides apply is worse
            # than not running at all.
            self.marker_error = str(e).split(": ", 1)[-1].splitlines()[0]
            return {}

    def read(self, rel: str) -> str | None:
        p = self.root / rel
        try:
            return p.read_text(encoding="utf-8") if p.is_file() else None
        except OSError:
            return None

    def exists_exactly(self, rel: str) -> bool:
        """Case-SENSITIVE presence test.

        Never Path.exists(): macOS and Windows are case-insensitive, so readme.md would pass
        there and fail on Linux — the same repo, two verdicts. See portability
        `case_sensitive_name_matching`.
        """
        return ritefs.exists_exactly(self.root / rel)

    def glob_matches(self, pattern: str) -> list[str]:
        """Every file matching a declared path_pattern, case-sensitively.

        Path.glob alone is not enough: on macOS and Windows it matches case-insensitively, so
        docs/plan-x.md would satisfy "docs/PLAN-*.md" there and not on Linux — the same repo,
        two verdicts, which is the failure case_sensitive_name_matching exists to prevent. Each
        hit is re-verified through ritefs.exists_exactly, so the guarantee is the same one
        exists_exactly gives.
        """
        out: list[str] = []
        for found in sorted(self.root.glob(pattern)):
            if not found.is_file():
                continue
            rel = found.relative_to(self.root).as_posix()
            if ritefs.exists_exactly(self.root / rel):
                out.append(rel)
        return out

    def resolve(self, rel: str) -> tuple[str, str | None]:
        """Find an artifact, honouring superseded conventions.

        The standard names docs/MISSION.md. Eleven existing projects predate that and use
        docs-yaml/MISSION.yaml — and migration is explicitly opt-in, never a side effect of
        other work. So a file found under a superseded directory or extension is PRESENT, not
        missing; the checker says where it actually is and what the canonical name would be.
        Reporting "missing MISSION" for a project that has one would be false, and a checker
        that cries wolf on 11 projects is a checker nobody runs.

        Returns (path_that_exists, note_if_non_canonical).
        """
        if self.exists_exactly(rel):
            return rel, None
        local = (self.spec.get("local") or {}).get("docs_dir") or {}
        canonical_dir = local.get("default", "docs")
        alts = local.get("alternatives") or []
        head, _, tail = rel.partition("/")
        if head != canonical_dir or not tail:
            return rel, None
        stem, dot, ext = tail.rpartition(".")
        for d in alts:
            for e in ([ext] + [x for x in ("yaml", "md") if x != ext]) if dot else [ext]:
                cand = f"{d}/{stem}.{e}"
                if self.exists_exactly(cand):
                    return cand, f"found as {cand}; canonical is {rel}"
        for e in ("yaml", "md"):
            if dot and e != ext:
                cand = f"{canonical_dir}/{stem}.{e}"
                if self.exists_exactly(cand):
                    return cand, f"found as {cand}; canonical is {rel}"
        return rel, None

    def threshold(self, artifact_id: str, rule: str, default):
        key = f"{artifact_id}.{rule}"
        return self.thresholds.get(key, default), key in self.thresholds


# ── helpers ─────────────────────────────────────────────────────────────────
_FM = re.compile(r"^---\s*\n(.*?)\n---\s*(\n|$)", re.S)
_LOG_LINE = re.compile(
    r"^(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2})(?::(\d{2}))?\s\|\s(\S+)\s\|\s(\S+)\s\|\s\[(\w+)\]\s"
)


def frontmatter(text: str):
    m = _FM.match(text)
    if not m:
        return None
    try:
        return riteyaml.load(m.group(1), "<front matter>") or {}
    except riteyaml.RiteYamlError:
        return None


def sections(text: str) -> list[str]:
    """H2 headings, which are the structure unit for a Markdown artifact."""
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", text, re.M)]


def section_body(text: str, name: str) -> str:
    parts = re.split(r"^##\s+", text, flags=re.M)
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        if head.strip() == name:
            return body
    return ""


def parse_date(v):
    if isinstance(v, str):
        try:
            return dt.date.fromisoformat(v.strip())
        except ValueError:
            return None
    return None


def newest_source_mtime(root: Path) -> dt.date | None:
    """Newest mtime of anything that is NOT documentation.

    Freshness is measured against the thing described, never against another document.
    Returns None for a documents-only project, where this measure degenerates — see
    c-freshness-thresholds-are-guesses.
    """
    newest, skip = None, {".git", "docs", "__pycache__", ".rite.yaml"}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if rel.parts[0] in skip or rel.name in {"README.md", "CLAUDE.md", "LOG.md", "HANDOFF.md"}:
            continue
        if rel.suffix in {".md"} and rel.parts[0] == "spec":
            continue
        ts = dt.date.fromtimestamp(p.stat().st_mtime)
        if newest is None or ts > newest:
            newest = ts
    return newest


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


# ── rules ───────────────────────────────────────────────────────────────────
# Each returns (severity, message). Absent from this table -> reported NA.
RULES = {}


def rule(name):
    def deco(fn):
        RULES[name] = fn
        return fn
    return deco


@rule("file_present")
def _file_present(ctx, art, test):
    if ctx.exists_exactly(art["path"]):
        return GREEN, "present"
    return RED, "missing"


@rule("min_lines")
def _min_lines(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    n, want = len(text.splitlines()), test.get("value", 1)
    return (GREEN, f"{n} lines") if n >= want else (YELLOW, f"{n} lines, want >= {want}")


@rule("no_placeholders")
def _no_placeholders(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    hits = [p for p in test.get("patterns", []) if p in text]
    return (GREEN, "none") if not hits else (YELLOW, "contains " + ", ".join(hits))


@rule("required_sections")
def _required_sections(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    have = {s.lower() for s in sections(text)}
    aliases = (art.get("structure") or {}).get("section_aliases") or {}
    missing = []
    for want in test.get("value", []) or (art.get("structure") or {}).get("required_sections", []):
        names = [want] + list(aliases.get(want, []))
        if not any(n.lower() in have for n in names):
            missing.append(want)
    return (GREEN, "all present") if not missing else (YELLOW, "missing: " + ", ".join(missing))


@rule("no_empty_sections")
def _no_empty_sections(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    empty = [s for s in sections(text) if not section_body(text, s).strip()]
    return (GREEN, "none empty") if not empty else (YELLOW, "empty: " + ", ".join(empty))


@rule("min_content_sections")
def _min_content_sections(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    n, want = len(sections(text)), test.get("value", 1)
    return (GREEN, f"{n} sections") if n >= want else (YELLOW, f"{n} sections, want >= {want}")


@rule("required_any_of_sections")
def _required_any_of(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    want = (art.get("structure") or {}).get("required_any_of_sections") or []
    have = {s.lower() for s in sections(text)}
    return (GREEN, "satisfied") if any(w.lower() in have for w in want) \
        else (YELLOW, "none of: " + ", ".join(want))


@rule("required_keys_present")
def _required_keys(ctx, art, test):
    doc = _load_yaml(ctx, art)
    if doc is None:
        return NA, "file absent or unparseable"
    want = (art.get("structure") or {}).get("required_keys") or []
    missing = [k for k in want if k not in doc]
    return (GREEN, "all present") if not missing else (YELLOW, "missing: " + ", ".join(missing))


@rule("as_of_present")
def _as_of(ctx, art, test):
    doc = _meta(ctx, art)
    if doc is None:
        return NA, "no provenance header found"
    return (GREEN, str(doc.get("as_of"))) if doc.get("as_of") else (YELLOW, "as_of missing")


@rule("as_of_within_days_of_activity")
def _as_of_fresh(ctx, art, test):
    doc = _meta(ctx, art)
    if doc is None:
        return NA, "no provenance header"
    as_of = parse_date(doc.get("as_of"))
    if as_of is None:
        return YELLOW, "as_of missing or unparseable"
    src = newest_source_mtime(ctx.root)
    if src is None:
        return NA, "documents-only project — no source to measure against"
    window, overridden = ctx.threshold(art["id"], "as_of_within_days_of_activity",
                                       test.get("value", 90))
    age = (src - as_of).days
    suffix = f" (window {window}d, overridden from {test.get('value')})" if overridden \
        else f" (window {window}d)"
    if age > window:
        return YELLOW, f"as_of {age}d behind newest source{suffix}"
    return GREEN, f"{max(age, 0)}d behind source{suffix}"


@rule("min_entries")
def _min_entries(ctx, art, test):
    want = test.get("value", 1)
    if art["path"].endswith(".md"):
        text = ctx.read(art["path"])
        if text is None:
            return NA, "file absent"
        n = sum(1 for ln in text.splitlines() if _LOG_LINE.match(ln))
    else:
        doc = _load_yaml(ctx, art)
        if doc is None:
            return NA, "file absent or unparseable"
        top = (art.get("structure") or {}).get("top_level_key")
        n = len(doc.get(top) or []) if top else 0
    return (GREEN, f"{n} entries") if n >= want else (YELLOW, f"{n} entries, want >= {want}")


@rule("entries_parse")
def _entries_parse(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    bad = [i + 1 for i, ln in enumerate(text.splitlines())
           if ln.strip() and not ln.startswith("#") and not _LOG_LINE.match(ln)]
    return (GREEN, "all parse") if not bad else (YELLOW, f"{len(bad)} unparseable (first: line {bad[0]})")


@rule("newest_entry_within_days_of_activity")
def _log_fresh(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    newest = None
    for ln in text.splitlines():
        m = _LOG_LINE.match(ln)
        if m:
            d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            newest = d if newest is None or d > newest else newest
    if newest is None:
        return YELLOW, "no parseable entries"
    src = newest_source_mtime(ctx.root)
    if src is None:
        return NA, "documents-only project — no source to measure against"
    window, overridden = ctx.threshold(art["id"], "newest_entry_within_days_of_activity",
                                       test.get("value", 30))
    age = (src - newest).days
    suffix = f" (window {window}d, overridden from {test.get('value')})" if overridden else ""
    if age > window:
        return YELLOW, f"source {age}d newer than the last log entry{suffix}"
    return GREEN, f"log current to within {max(age, 0)}d{suffix}"


@rule("min_list_items")
def _min_list_items(ctx, art, test):
    doc = _load_yaml(ctx, art)
    if doc is None:
        return NA, "file absent or unparseable"
    key = test.get("key")
    n = len(doc.get(key) or [])
    want = test.get("value", 1)
    return (GREEN, f"{key}: {n}") if n >= want else (YELLOW, f"{key}: {n}, want >= {want}")


@rule("entry_required_keys")
def _entry_keys(ctx, art, test):
    doc = _load_yaml(ctx, art)
    if doc is None:
        return NA, "file absent or unparseable"
    st = art.get("structure") or {}
    top = st.get("top_level_key") or (st.get("top_level_keys") or [None])[0]
    want = ((st.get("entry") or {}).get("required_keys")) or []
    bad = []
    for e in doc.get(top) or []:
        if isinstance(e, dict):
            miss = [k for k in want if k not in e]
            if miss:
                bad.append(f"{e.get('id', '?')}: {'/'.join(miss)}")
    return (GREEN, "all entries complete") if not bad \
        else (YELLOW, f"{len(bad)} incomplete ({bad[0]})")


@rule("unique_ids")
def _unique_ids(ctx, art, test):
    doc = _load_yaml(ctx, art)
    if doc is None:
        return NA, "file absent or unparseable"
    st = art.get("structure") or {}
    top = st.get("top_level_key") or (st.get("top_level_keys") or [None])[0]
    ids = [e.get("id") for e in (doc.get(top) or []) if isinstance(e, dict)]
    dupes = {i for i in ids if ids.count(i) > 1}
    return (GREEN, f"{len(ids)} unique") if not dupes else (RED, "duplicates: " + ", ".join(map(str, dupes)))


@rule("no_dangling_supersedes")
def _no_dangling(ctx, art, test):
    doc = _load_yaml(ctx, art)
    if doc is None:
        return NA, "file absent or unparseable"
    entries = doc.get("decisions") or []
    ids = {e.get("id") for e in entries if isinstance(e, dict)}
    dangling = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        for k in ("supersedes", "superseded_by", "amends"):
            v = e.get(k)
            for ref in ([v] if isinstance(v, str) else (v or [])):
                if ref and ref not in ids:
                    dangling.append(f"{e.get('id')}.{k} -> {ref}")
    return (GREEN, "all resolve") if not dangling else (RED, "; ".join(dangling[:3]))


@rule("append_only_preserved")
def _append_only(ctx, art, test):
    if not ctx.is_git:
        return NA, "requires revision history — no git repository"
    removed = git_removed_lines(ctx.root, art["path"])
    if removed is None:
        return NA, "requires revision history — file not tracked"
    return (GREEN, "additions only") if removed == 0 \
        else (RED, f"{removed} existing line(s) changed or removed")


@rule("milestones_append_only")
def _milestones_append_only(ctx, art, test):
    if not ctx.is_git:
        return NA, "requires revision history — no git repository"
    z = zone_of(ctx.root, art["path"], "milestones")
    if z is None:
        return NA, "requires revision history — file not tracked or unparseable"
    old, new = z
    old, new = old or [], new or []
    if new[:len(old)] == old:
        added = len(new) - len(old)
        return GREEN, f"{len(old)} preserved" + (f", {added} appended" if added else "")
    return RED, "an existing milestone was changed, reordered or removed"


@rule("required_frontmatter_present")
def _required_fm(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    fm = frontmatter(text)
    if fm is None:
        return YELLOW, "no front matter"
    want = list(((art.get("structure") or {}).get("required_frontmatter") or {}).keys())
    missing = [k for k in want if k not in fm]
    return (GREEN, "complete") if not missing else (YELLOW, "missing: " + ", ".join(missing))


@rule("not_expired")
def _not_expired(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    fm = frontmatter(text) or {}
    if str(fm.get("status", "")).lower() == "spent":
        return YELLOW, f"status: spent — {art['path']} is stale and still present"
    raw = str(fm.get("expires", ""))
    m = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    if not m:
        return YELLOW, "expires carries no date (a date is required; a condition may accompany it)"
    d = dt.date.fromisoformat(m.group(0))
    if d < ctx.today:
        return YELLOW, f"expired {(ctx.today - d).days}d ago ({d})"
    return GREEN, f"live until {d}"


@rule("session_end_decision_recorded")
def _session_end(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    fm = frontmatter(text) or {}
    v = fm.get("session_end")
    ok = {"written", "updated", "carried_forward", "none"}
    if v in ok:
        return GREEN, f"session_end: {v}"
    return YELLOW, "session_end missing or not one of " + "/".join(sorted(ok))


@rule("written_not_older_than_newest_log_entry")
def _written_vs_log(ctx, art, test):
    text = ctx.read(art["path"])
    log = ctx.read("LOG.md")
    if text is None or log is None:
        return NA, "HANDOFF or LOG absent"
    fm = frontmatter(text) or {}
    written = parse_date(fm.get("written"))
    if written is None:
        return YELLOW, "written missing or unparseable"
    newest = None
    for ln in log.splitlines():
        m = _LOG_LINE.match(ln)
        if m:
            d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            newest = d if newest is None or d > newest else newest
    if newest is None:
        return NA, "no parseable log entries"
    if written < newest:
        return YELLOW, f"handoff written {written}, newest log entry {newest} — session did not close"
    return GREEN, f"written {written}, log current to {newest}"


@rule("inception_present")
def _inception(ctx, art, test):
    doc = _load_yaml(ctx, art)
    if doc is None:
        return NA, "file absent or unparseable"
    return (GREEN, "present") if doc.get("inception") else (YELLOW, "no inception block — drift is unmeasurable")


@rule("inception_unchanged")
def _inception_unchanged(ctx, art, test):
    if not ctx.is_git:
        return NA, "requires revision history — no git repository"
    z = zone_of(ctx.root, art["path"], "inception")
    if z is None:
        return NA, "requires revision history — file not tracked or unparseable"
    old, new = z
    if old is None:
        return NA, "no inception block at HEAD to compare against"
    return (GREEN, "write-once zone intact") if old == new \
        else (RED, "the inception block was edited — it is set once, at project birth")


@rule("no_done_markers")
def _no_done(ctx, art, test):
    doc = _load_yaml(ctx, art)
    if doc is None:
        return NA, "file absent or unparseable"
    items = ((doc.get("near_term") or {}).get("candidates")) or []
    bad = [i.get("id") for i in items
           if isinstance(i, dict) and str(i.get("status", "")).lower() in {"done", "completed", "finished"}]
    return (GREEN, "none") if not bad else (YELLOW, "marked done in place: " + ", ".join(map(str, bad)))


@rule("no_provenance_header")
def _no_prov(ctx, art, test):
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    if frontmatter(text) is not None or re.search(r"^schema_version:", text, re.M):
        return RED, "LICENSE must NOT carry a provenance header — it is verbatim third-party text"
    return GREEN, "verbatim, no header"


# ── the declared claim surface ──────────────────────────────────────────────
# The one place in this checker where configuration comes from the ARTIFACT BEING CHECKED
# rather than from the standard. Every other rule reads test["value"] or art["structure"];
# these read a claims block out of the document itself, because the claims a project makes
# about its own tree are the project's to state, not the standard's to know.
#
# This is what unparks claims_match_filesystem. MISSION forbids inference at check time, so
# prose cannot be read — and prose is where the rot lives. A path is the smallest thing in a
# document that a human will write and a machine can falsify.
#
# LIMIT, stated rather than hidden: path-shaped claims only. "session_start writes status.json"
# is a claim about BEHAVIOUR and passes untouched. Three of the four real failures of
# 2026-09-08/09 were path-shaped; the fourth was not.
#
# TWO LOCATIONS, and not as a compromise. The provenance header is required only in the docs
# directory (provenance_header.required_in), so README.md and CLAUDE.md deliberately carry
# none — and YAML front matter at the top of a README is rendered by the forge on the
# repository's landing page, degrading the file this standard itself calls the highest-value
# one in the repo. A root-level Markdown file therefore declares claims in an HTML comment,
# which renders as nothing. Same parser, same shape, one extra place to look.
_CLAIM_DIRECTIONS = ("absent", "present")
_CLAIMS_COMMENT = re.compile(r"<!--\s*rite:claims\s*\n(.*?)-->", re.S)


def _claims_block(ctx, art):
    """(claims, error) — the mapping or None, plus why a block present but unusable is bad."""
    meta = _meta(ctx, art)
    if isinstance(meta, dict) and meta.get("claims") is not None:
        return meta.get("claims"), None
    text = ctx.read(art["path"])
    if text is None or not art["path"].endswith(".md"):
        return None, None
    m = _CLAIMS_COMMENT.search(text)
    if not m:
        return None, None
    try:
        return riteyaml.load(m.group(1), art["path"] + " (rite:claims)"), None
    except riteyaml.RiteYamlError as e:
        return None, f"the rite:claims comment does not parse — {str(e).split(': ', 1)[-1]}"


@rule("filename_matches_canonical")
def _filename_matches_canonical(ctx, art, test):
    """Every instance of a many-instance artifact is named the canonical way.

    THE SHAPE IS DECLARED BY THE ARTIFACT, not held here. The first version hardcoded the PLAN
    regex in the checker, which was wrong twice over: it is a hardcoded value with no
    human-visible home, and it silently mis-judged the next artifact to declare this rule —
    script_copy, whose leaf is an arbitrary filename under a dated directory. Both now carry
    `canonical_name_pattern` and the checker only applies it.

    Reachable at all only since path_pattern existed. Before that the artifact was matched
    literally against "docs/PLAN-YYYY-MM-DD-<slug>.md", so this rule had never once run against
    a real plan copy — c-pattern-paths-are-matched-literally.
    """
    pattern = art.get("path_pattern")
    if not pattern:
        return NA, "artifact declares no path_pattern"
    shape = art.get("canonical_name_pattern")
    if not shape:
        return NA, "artifact declares no canonical_name_pattern"
    found = ctx.glob_matches(pattern)
    if not found:
        return NA, "no instances present"
    try:
        want = re.compile(shape)
    except re.error as exc:
        return YELLOW, f"canonical_name_pattern does not compile — {exc}"
    bad = [f for f in found if not want.match(f)]
    if bad:
        named = art.get("structure", {}).get("canonical_name", shape)
        head = ", ".join(bad[:3]) + (f" and {len(bad) - 3} more" if len(bad) > 3 else "")
        return YELLOW, f"{len(bad)} of {len(found)} not named {named}: {head}"
    return GREEN, f"{len(found)} instance(s) canonically named"


@rule("source_plans_all_copied")
def _source_plans_all_copied(ctx, art, test):
    """A plan this project's own session WROTE, with no copy here, fails.

    Attribution is authorship, never mention: a transcript that merely lists the plans
    directory does not own its contents. See rite_copy._authored_in, which learned that the
    hard way.
    """
    try:
        import rite_copy
    except ImportError as exc:
        return NA, f"cannot load the copier — {exc}"
    if not rite_copy.PLANS_DIR.is_dir():
        return NA, "no plans directory on this machine"
    missing = rite_copy.uncopied_plans(ctx.root)
    if missing is None:
        return NA, "no session transcripts to attribute against"
    if missing:
        return YELLOW, (f"{len(missing)} plan(s) written by this project are not copied here: "
                        + ", ".join(missing) + " — run rite_copy.py --plans")
    return GREEN, "every plan this project wrote has a copy here"


@rule("mirror_not_stale")
def _mirror_not_stale(ctx, art, test):
    """A memory newer than the mirror's last sync means the mirror is lying by omission."""
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    try:
        import rite_copy
    except ImportError as exc:
        return NA, f"cannot load the copier — {exc}"
    memdir = rite_copy.memory_dir_for(ctx.root)
    if memdir is None:
        return NA, "no memory folder for this project"
    stamp = re.search(r"^> Last sync: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})$", text, re.MULTILINE)
    if not stamp:
        return YELLOW, "no `Last sync` line — cannot tell whether this mirror is current"
    try:
        synced = dt.datetime.strptime(stamp.group(1), "%Y-%m-%d %H:%M")
    except ValueError:
        return YELLOW, f"unreadable sync stamp {stamp.group(1)!r}"
    files = rite_copy.memory_files(memdir)
    if not files:
        return NA, "no memory files"
    # The stamp has minute resolution, so a memory written in the same minute as the sync is
    # not evidence of staleness. Only a file newer than the END of that minute counts.
    newest = max(f.stat().st_mtime for f in files)
    if newest > (synced + dt.timedelta(minutes=1)).timestamp():
        when = dt.datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M")
        return YELLOW, (f"a memory changed at {when}, after the mirror synced at "
                        f"{stamp.group(1)} — run rite_copy.py --memory")
    return GREEN, f"{len(files)} memories, synced {stamp.group(1)}"


@rule("claims_declared")
def _claims_declared(ctx, art, test):
    if ctx.read(art["path"]) is None:
        return NA, "file absent"
    block, err = _claims_block(ctx, art)
    if err:
        return YELLOW, err
    if block is None:
        return YELLOW, ("no claims declared — this document asserts nothing that can be "
                        "falsified against the tree")
    return GREEN, "declares claims"


@rule("claims_match_filesystem")
def _claims_match_filesystem(ctx, art, test):
    if ctx.read(art["path"]) is None:
        return NA, "file absent"
    claims, err = _claims_block(ctx, art)
    if err:
        return RED, err
    if claims is None:
        # Nothing to verify. The NUDGE to declare something is claims_declared's job, at a
        # different level and a different severity; one verdict cannot answer two questions.
        return NA, "no claims declared — nothing to verify"

    # A malformed block is RED, never skipped. A claim surface that silently does nothing is
    # the exact defect this rule exists to remove, reintroduced one layer down.
    if not isinstance(claims, dict):
        return RED, f"claims must be a mapping of {'/'.join(_CLAIM_DIRECTIONS)}, got a scalar"
    unknown = [k for k in claims if k not in _CLAIM_DIRECTIONS]
    if unknown:
        return RED, (f"unknown claim direction(s): {', '.join(map(str, unknown))} — "
                     f"expected {' and/or '.join(_CLAIM_DIRECTIONS)}")
    for direction in _CLAIM_DIRECTIONS:
        val = claims.get(direction)
        if val is not None and not (isinstance(val, list)
                                    and all(isinstance(x, str) for x in val)):
            return RED, f"claims.{direction} must be a list of paths"

    broken = []
    for direction in _CLAIM_DIRECTIONS:
        want_present = direction == "present"
        for rel in claims.get(direction) or []:
            # exists_exactly, never Path.exists: a claim passing on macOS and failing on Linux
            # is one repo with two verdicts. d-one-implementation-of-a-portability-rule.
            if ctx.exists_exactly(rel) is not want_present:
                broken.append(f"{rel} claimed {direction} but is "
                              f"{'absent' if want_present else 'present'}")
    if broken:
        return RED, "; ".join(broken)
    n = sum(len(claims.get(d) or []) for d in _CLAIM_DIRECTIONS)
    return GREEN, f"{n} claim(s) hold"


# `required_from_stage` was a RULE here until 2026-09-10, declared only by LICENSE. It is now
# an engine gate applying to every artifact — Ctx.not_yet_required() — so keeping the rule as
# well would be two implementations of one decision, which is how the two of them drift apart.
# Deleted rather than left dead: this repo already carries required_any_of_sections, which is
# implemented and declared by nothing, and one such is enough.


def parse_failure(ctx, rel: str) -> str | None:
    """Why `rel` cannot be parsed, or None if it can. Absence is NOT a failure.

    This is the distinction c-na-conflates-absent-with-unparseable existed for. "File absent
    or unparseable" covered two opposite situations under one benign-looking verdict: a file
    the project never wrote, and a file Rite cannot read. The first is often fine. The second
    means the checker is failing while looking calm — and on 2026-09-09 it hid four real
    parser refusals across two projects, nine NA lines deep.
    """
    text = ctx.read(rel)
    if text is None:
        return None  # absent — a different question, answered by the exists tests
    body = text
    if rel.endswith(".md"):
        m = _FM.match(text)
        if not m:
            return None  # no front matter is a populated-test concern, not a parse failure
        body = m.group(1)
    elif not rel.endswith((".yaml", ".yml")):
        return None
    try:
        riteyaml.load(body, rel)
    except riteyaml.RiteYamlError as e:
        return str(e).split(": ", 1)[-1].strip()
    return None


def _load_yaml(ctx, art):
    text = ctx.read(art["path"])
    if text is None:
        return None
    try:
        return riteyaml.load(text, art["path"]) or {}
    except riteyaml.RiteYamlError:
        return None


def _meta(ctx, art):
    """The provenance header, wherever it lives: front matter in .md, top level in .yaml."""
    text = ctx.read(art["path"])
    if text is None:
        return None
    if art["path"].endswith(".md"):
        return frontmatter(text)
    try:
        return riteyaml.load(text, art["path"]) or {}
    except riteyaml.RiteYamlError:
        return None


# ── engine ──────────────────────────────────────────────────────────────────
def check(root: Path, spec: dict,
          excluded_scopes: set[str] | None = None) -> tuple[list[Finding], dict]:
    ctx = Ctx(root, spec, excluded_scopes)
    findings: list[Finding] = []
    declared = implemented = 0

    # Which version of the standard this project targets. Absent means "current", which is the
    # common case and is silent. A mismatch is YELLOW and never RED: Rite does not keep old
    # rule sets, so it cannot honour a pin — and a compatibility promise it cannot honour is
    # worse than none. Reporting the gap is the honest half. See d-standard-version-declared.
    want_version = (ctx.marker or {}).get("standard_version")
    have_version = spec.get("schema_version")
    if want_version and have_version and str(want_version) != str(have_version):
        findings.append(Finding(
            YELLOW, "project", "fresh", "standard_version", ritefs.MARKER,
            f"targets standard {want_version}; this is {have_version}. Rite runs the CURRENT "
            f"rules — it keeps no old rule sets — so the gap is reported, never honoured"))

    for art in spec.get("artifacts", []):
        tier = art.get("tier", 9)
        # AN ARTIFACT WITH MANY INSTANCES IS MATCHED BY GLOB, NOT BY NAME. plan_copy's `path`
        # is a shape, "docs/PLAN-YYYY-MM-DD-<slug>.md", and comparing it literally meant the
        # artifact was absent on every project that ever existed — including this one, with two
        # plan copies on disk. c-pattern-paths-are-matched-literally. `path` stays the display
        # name; presence is the glob. resolve() is skipped for these: it exists to find a file
        # under a superseded directory, and a pattern artifact has no single file to find.
        instances: list[str] = []
        pattern = art.get("path_pattern")
        if pattern:
            instances = ctx.glob_matches(pattern)
            present = bool(instances)
        else:
            actual, note = ctx.resolve(art["path"])
            if note:
                art = dict(art, path=actual)
                findings.append(Finding(YELLOW, "project", "populated", "canonical_name",
                                        actual, note))
            present = ctx.exists_exactly(art["path"])
        # A DECLARATION BEATS TIER; tier is only the fallback. Where the artifact declares
        # required_from_stage AND the project declares a stage, the stage decides outright:
        # absent-and-not-yet-due is NA naming the stage, absent-and-due is RED. Tier is
        # consulted only when one of the two declarations is missing — see the spec's
        # `no_stage_declared`, since deleting one line from .rite.yaml must not silence the
        # standard.
        #
        # Getting this wrong once is instructive: an earlier version asked `tier >= 2 or ...`,
        # which let tier short-circuit the stage. LICENSE is tier 2 and required from `shipped`,
        # so it stayed optional at EVERY stage and a project could publish with no licence —
        # the exact failure required_from_stage was introduced to prevent. Caught by the stage
        # progression fixture expecting 8 at `shipped` and seeing 7.
        stage_note = ctx.not_yet_required(art)
        stage_decides = art.get("required_from_stage") is not None and ctx.stage_index is not None
        if stage_decides:
            optional_absent = stage_note is not None and not present
        else:
            optional_absent = tier >= 2 and not present

        # A present file that cannot be parsed is a RED in its own right, reported ONCE.
        # Its remaining tests are not run, and say so in one line rather than as a cascade
        # of NAs that each look like an optional file quietly missing.
        broken = parse_failure(ctx, art["path"]) if present else None
        if broken:
            findings.append(Finding(RED, "project", "integrity", "parseable",
                                    art["path"], broken))
            skipped = 0
            for test in art.get("tests") or []:
                declared += 1
                if test.get("rule") in RULES:
                    implemented += 1
                if test.get("rule") not in ("optional",):
                    skipped += 1
            if skipped:
                findings.append(Finding(NA, "project", "exists", "checks_not_run",
                                        art["path"],
                                        f"{skipped} further checks not run — the file could "
                                        f"not be parsed, so nothing about it is known"))
            continue

        for test in art.get("tests") or []:
            declared += 1
            rule_name = test.get("rule")
            # Coverage is about what this checker CAN do, not about which files this
            # project happens to carry — otherwise an absent optional artifact would
            # read as missing checker capability.
            if rule_name in RULES:
                implemented += 1
            level = test.get("level", "exists")
            severity_if_failed = LEVEL_SEVERITY.get(level, YELLOW)

            if rule_name in ctx.disabled:
                findings.append(Finding(NA, "project", level, rule_name, art["path"],
                                        "disabled in .rite.yaml"))
                continue
            # A caller may exclude a whole scope — CI excludes `session`, whose verdict
            # depends on whether the session running right now has closed. Reported, never
            # silent: a check that vanished and a check that passed must not look alike.
            if test.get("scope") and test["scope"] in ctx.excluded_scopes:
                findings.append(Finding(NA, "project", level, rule_name, art["path"],
                                        f"{test['scope']}-scoped — excluded by "
                                        f"--exclude-scope={test['scope']}"))
                continue
            if rule_name in ("optional",):
                continue
            if optional_absent:
                findings.append(Finding(
                    NA, "project", level, rule_name, art["path"],
                    stage_note or f"tier {tier}, not present — optional",
                    deferred_to=art.get("required_from_stage") if stage_note else None))
                continue

            fn = RULES.get(rule_name)
            if fn is None:
                findings.append(Finding(NA, "project", level, rule_name, art["path"],
                                        "declared in the spec, not implemented by this checker"))
                continue
            try:
                sev, msg = fn(ctx, art, test)
            except Exception as exc:  # a rule must never take the run down
                findings.append(Finding(NA, "claude", level, rule_name, art["path"],
                                        f"rule raised {type(exc).__name__}: {exc}"))
                continue
            if sev in (RED, YELLOW):
                sev = severity_if_failed if sev != NA else NA
            findings.append(Finding(sev, "project", level, rule_name, art["path"], msg))

    return findings, {"declared": declared, "implemented": implemented, "ctx": ctx}


def report(root: Path, findings: list[Finding], meta: dict) -> int:
    ctx = meta["ctx"]
    counts = {s: sum(1 for f in findings if f.severity == s) for s in (RED, YELLOW, GREEN, NA)}
    width = max((len(f.path) for f in findings), default=10)

    print(f"rite — {root.name}")
    print()
    if ctx.marker_error:
        print(f"  {RED:6} project  integrity  {'.rite.yaml':30}  unparseable — "
              f"{ctx.marker_error}")
        print(f"  {'':6} {'':8} {'':10} {'':30}  every threshold and override in it was "
              f"ignored; defaults were used")
        print()
    # STAGE-DEFERRED CHECKS ARE COLLAPSED, NOT DROPPED. Measured on 2026-09-10: a project at
    # stage `idea` printed 54 lines to convey ONE finding, 46 of them saying "not required
    # before stage X". Stage gating had replaced a wall of RED with a wall of NA, and
    # d-stage-gates-the-standard exists precisely because a tool that opens by listing
    # everything you have not done yet gets uninstalled the next day.
    #
    # They are summarised rather than hidden: the count and the artifacts are both still
    # stated, so a check that is waiting and a check that passed still do not look alike. They
    # remain in `findings` and in the NA count above, which is what keeps the totals honest.
    deferred: dict[str, list[str]] = {}
    for f in findings:
        if f.deferred_to:
            names = deferred.setdefault(f.deferred_to, [])
            if f.path not in names:
                names.append(f.path)

    for f in findings:
        if f.severity == GREEN or f.deferred_to:
            continue
        print(f"  {f.severity:6} {f.side:8} {f.level:10} {f.path:{width}}  "
              f"{f.rule} — {f.message}")

    if deferred:
        order = ctx.spec.get("stage_vocabulary", {}).get("values", [])
        total = sum(1 for f in findings if f.deferred_to)
        print(f"  {NA:6} {'project':8} {'—':10} {total} checks not required at stage "
              f"{ctx.stage!r}, waiting on:")
        for stage in sorted(deferred, key=lambda s: order.index(s) if s in order else 99):
            print(f"  {'':6} {'':8} {'':10}   {stage:8} {', '.join(deferred[stage])}")

    if not (counts[RED] or counts[YELLOW] or counts[NA]):
        print("  all checks green")
    print()
    print(f"  {len(findings)} checks · {counts[RED]} RED · {counts[YELLOW]} YELLOW · "
          f"{counts[NA]} NA · {counts[GREEN]} GREEN")
    print(f"  coverage: {meta['implemented']} of {meta['declared']} declared tests implemented")
    if not ctx.is_git:
        print("  no git repository — integrity checks report NA (capability, not prerequisite)")

    fail_on = str(ctx.fail_on).lower()
    if fail_on == "none":
        return 0
    if counts[RED] or (fail_on == "yellow" and counts[YELLOW]):
        return 1
    return 0


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    force = "--force" in argv
    # `--exclude-scope=session`, not `--exclude-scope session`: the joined form keeps the
    # value out of the positional list, which is how the project directory is found.
    excluded_scopes = {
        a.split("=", 1)[1].strip()
        for a in argv[1:]
        if a.startswith("--exclude-scope=") and a.split("=", 1)[1].strip()
    }
    root = Path(args[0]).resolve() if args else Path.cwd()
    if not ritefs.marker_present(root) and not force:
        # Opt-in. Silent where not invited — see participation in the spec.
        # --force answers "what would this project score if it opted in?", which is the
        # only way to evaluate before adopting. It reads; it never writes.
        return 0
    try:
        spec = riteyaml.load(SPEC_PATH.read_text(encoding="utf-8"), str(SPEC_PATH))
    except riteyaml.RiteYamlError as exc:
        print(f"FAIL  cannot read the standard: {exc}", file=sys.stderr)
        return 1
    findings, meta = check(root, spec, excluded_scopes)
    return report(root, findings, meta)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
