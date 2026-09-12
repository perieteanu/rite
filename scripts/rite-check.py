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
import riterules  # noqa: E402
from riterules import git_removed_lines, git_show, zone_of  # noqa: E402,F401

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


# ── rules ───────────────────────────────────────────────────────────────────
# Each returns (severity, message). Absent from this table -> reported NA.
RULES = {}

# Rules that are MARKERS rather than checks: they declare something about the artifact and are
# handled by an explicit branch, never by a RULES entry. They are excluded from the coverage
# denominator, because "unimplemented" should mean work outstanding.
MARKER_RULES = frozenset({"optional"})


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
    """One of the declared topology sections, counting declared aliases.

    THE ALIASES WERE BEING IGNORED. `section_aliases` sits in the same `structure:` block and
    says "Summary" satisfies "Shape"; the rule compared against the primary names only, so a
    document doing exactly what the spec permits would have been reported as missing all of
    them. Never noticed, because until 2026-09-10 no artifact declared this rule and it had
    never run on anything.
    """
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    structure = art.get("structure") or {}
    want = structure.get("required_any_of_sections") or []
    if not want:
        return NA, "the artifact declares no required_any_of_sections"
    aliases = structure.get("section_aliases") or {}
    have = {s.lower() for s in sections(text)}
    for primary in want:
        accepted = [primary, *(aliases.get(primary) or [])]
        if any(a.lower() in have for a in accepted):
            return GREEN, f"{primary} present" if primary.lower() in have \
                else f"satisfied by an alias of {primary}"
    waived = structure.get("required_any_of_waived_when")
    note = " — waived where the top-level keys ARE the topology" if waived else ""
    return YELLOW, "none of: " + ", ".join(want) + note


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


@rule("no_future_timestamps")
def _no_future_timestamps(ctx, art, test):
    """A dated entry later than now. See riterules.log_future_timestamps for the reasoning.

    Shares its predicate with the PostToolUse watcher, which asks the same question the instant
    a write lands. One implementation, two consumers — two copies would be free to disagree
    about what "future" means, which is the drift this project attacks everywhere else.
    """
    text = ctx.read(art["path"])
    if text is None:
        return NA, "file absent"
    future = riterules.log_future_timestamps(text)
    if future:
        return RED, (f"{len(future)} entry/entries dated in the future — a timestamp that was "
                     f"extrapolated, not read. First: {future[0]}")
    return GREEN, "no entry is dated later than now"


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


@rule("deleted_ids_appear_in_milestones")
def _deleted_ids_appear(ctx, art, test):
    """An id that left near_term must have become a milestone — or moved, not vanished.

    THE LAST DECLARED RULE TO BE IMPLEMENTED. Deleting a closed item is the convention rather
    than marking it done in place, and that is only safe if the item is PROMOTED rather than
    erased. Without this check the convention was a rule with no completion test, which is the
    one thing this project exists to abolish.

    A DELETION IS NOT ALWAYS A CLOSURE, and the check would be wrong without that. Items
    legitimately MOVE between lists: ci-portability-matrix, setup-hook-scaffolding and
    publish-github all went mid_term -> near_term on 2026-09-10, which looks identical to a
    deletion if only one list is read. So an id that left near_term is satisfied by appearing
    in milestones OR in any other roadmap list.
    """
    if not ctx.is_git:
        return NA, "requires revision history — no git repository"
    z = zone_of(ctx.root, art["path"], "near_term")
    if z is None:
        return NA, "requires revision history — file not tracked or unparseable"
    old_nt, new_nt = z

    def ids(block):
        if not isinstance(block, dict):
            return set()
        return {c.get("id") for c in (block.get("candidates") or [])
                if isinstance(c, dict) and c.get("id")}

    gone = ids(old_nt) - ids(new_nt)
    if not gone:
        return GREEN, "no near_term id was removed"

    try:
        doc = riteyaml.load((ctx.root / art["path"]).read_text(encoding="utf-8"), art["path"])
    except (riteyaml.RiteYamlError, OSError):
        return NA, "the current file could not be parsed"

    landed = {m.get("id") for m in (doc.get("milestones") or [])
              if isinstance(m, dict) and m.get("id")}
    elsewhere = set()
    for key in ("mid_term", "long_term"):
        for item in doc.get(key) or []:
            if isinstance(item, dict) and item.get("id"):
                elsewhere.add(item["id"])

    lost = sorted(i for i in gone if i not in landed and i not in elsewhere)
    if lost:
        return RED, (f"{len(lost)} near_term id(s) removed without a milestone and not moved "
                     f"to another list: {', '.join(lost)}. Deleting is how an item closes — but "
                     f"only if it is promoted, never erased.")
    moved = sorted(i for i in gone if i not in landed)
    note = f" ({len(moved)} moved, not closed)" if moved else ""
    return GREEN, f"{len(gone)} removed id(s) accounted for{note}"


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
                        + ", ".join(missing) + " — run /rite:end, or rite.sh copy --plans")
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
    files = rite_copy.memory_files(memdir)
    if not files:
        return NA, "no memory files"
    stamp = rite_copy.mirror_stamp(text)
    if stamp is None:
        return YELLOW, "no readable `Last sync` line — cannot tell whether this mirror is current"
    # ONE PREDICATE, shared with the copier. Two implementations disagreed within the hour they
    # both existed: the copier skipped rewriting when content matched and the checker judged by
    # the stamp, so a stale stamp over correct content stayed YELLOW and the checker's own
    # advice fixed nothing.
    if rite_copy.mirror_is_stale(memdir.parent, text, files):
        when = dt.datetime.fromtimestamp(max(f.stat().st_mtime for f in files))
        return YELLOW, (f"a memory changed at {when:%Y-%m-%d %H:%M}, after the mirror synced at "
                        f"{stamp:%Y-%m-%d %H:%M} — run /rite:end, or rite.sh copy --memory")
    return GREEN, f"{len(files)} memories, synced {stamp:%Y-%m-%d %H:%M}"


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
    # Paths an artifact already accounts for. The project-wide YAML rules skip these: an
    # unparseable ROADMAP is one finding from `parseable`, and reporting it again as a project
    # YAML failure would be two findings for one cause — the cascade d-unparseable-is-red-absent-
    # is-na exists to prevent.
    covered: set[str] = set()

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
        covered.add(art["path"])
        covered.update(instances)

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
                if test.get("rule") in MARKER_RULES:
                    continue
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
            rule_name = test.get("rule")
            # Coverage is about what this checker CAN do, not about which files this
            # project happens to carry — otherwise an absent optional artifact would
            # read as missing checker capability.
            #
            # `optional` IS NOT A RULE AWAITING IMPLEMENTATION. It is a marker meaning the
            # artifact is not required, handled by its own branch and deliberately absent from
            # RULES. Counting it in the denominator understated the checker by four instances
            # and, worse, four documents repeated "seven declared tests unimplemented" for days
            # on the strength of that line, read as a to-do list it never was.
            # c-coverage-counts-optional-as-unimplemented.
            if rule_name in MARKER_RULES:
                continue
            declared += 1
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

    # ── the YAML the project carries that is not an artifact ──────────────────
    # THE GAP THIS CLOSES, measured: peugeot307sw committed broken YAML twice while `rite check`
    # scored it 0 RED, because docs/WORKLIST.yaml and docs/FAULTS.yaml are not in the inventory.
    # A fixture with a broken docs/WORKLIST.yaml still scores 0 RED at every stage without this.
    # c-project-yaml-is-not-checked, ruled by the user 2026-09-11: check them.
    yaml_findings, yaml_declared, yaml_implemented = project_yaml_findings(ctx, covered)
    findings.extend(yaml_findings)
    declared += yaml_declared
    implemented += yaml_implemented

    return findings, {"declared": declared, "implemented": implemented, "ctx": ctx}


# The project-wide rules this checker implements, by the name the spec declares. A rule declared
# in `yaml_subset.tests` and absent here is reported NA as unimplemented, exactly as an artifact
# rule would be — the coverage line must never flatter the checker.
PROJECT_RULES = frozenset({"yaml_parses", "yaml_within_subset"})
_SEV = {"RED": RED, "YELLOW": YELLOW, "GREEN": GREEN, "NA": NA}


def project_yaml_findings(ctx, covered: set[str]) -> tuple[list[Finding], int, int]:
    """Check every YAML file in scope, not only the declared artifacts.

    ONE FINDING PER PROBLEM FILE, and one summary finding per rule when nothing is wrong. Each
    bad file is a distinct defect a reader must act on, unlike the stage-deferred wall where 46
    lines carried one fact — so these are not collapsed. When every file is clean the rule still
    lands in the totals, because a check that ran and a check that did not must not look alike.
    """
    section = ctx.spec.get("yaml_subset") or {}
    tests = [t for t in (section.get("tests") or []) if t.get("rule")]
    if not tests:
        return [], 0, 0

    files, stats = riterules.project_yaml_files(ctx.root, ctx.spec, ctx.marker)
    checkable = [rel for rel in files if rel not in covered]
    by_kind: dict[str, list[tuple[str, str, str]]] = {"invalid": [], "unsupported": []}
    for rel in checkable:
        verdict = riterules.yaml_verdict(ctx.root / rel, rel)
        if verdict is None:
            continue
        kind, construct, message = verdict
        by_kind.setdefault(kind, []).append((rel, construct, message))

    out: list[Finding] = []
    if stats["declared_globs"] or stats["excluded"]:
        # Reported, never silent — the rule overrides_are_never_silent, applied to scope.
        out.append(Finding(
            NA, "project", "populated", "yaml_check", ritefs.MARKER,
            f"scope declared in .rite.yaml: {stats['declared_globs']} extra glob(s), "
            f"{stats['excluded']} file(s) excluded"))
    elif not checkable:
        # ONE line, not one per rule. Both rules had nothing to read and that is a single fact
        # about the project; saying it twice is the wall of near-identical NAs that
        # d-stage-deferred-checks-are-collapsed exists to prevent, in miniature. It is still said,
        # because a check that found nothing to read and a check that passed must not look alike.
        out.append(Finding(
            NA, "project", "integrity", "yaml_check", ".",
            "no YAML files in scope — yaml_parses and yaml_within_subset read nothing"))

    declared = implemented = 0
    for test in tests:
        rule = str(test["rule"])
        declared += 1
        if rule not in PROJECT_RULES:
            out.append(Finding(NA, "project", str(test.get("level", "integrity")), rule, ".",
                               "declared in the spec, not implemented by this checker"))
            continue
        implemented += 1
        level = str(test.get("level", "integrity"))
        severity = _SEV.get(str(test.get("severity")), RED)
        if rule in ctx.disabled:
            out.append(Finding(NA, "project", level, rule, ritefs.MARKER,
                               "disabled in .rite.yaml"))
            continue
        if not checkable:
            continue  # already stated once above, for both rules together
        kind = "invalid" if rule == "yaml_parses" else "unsupported"
        hits = by_kind.get(kind) or []
        if not hits:
            out.append(Finding(GREEN, "project", level, rule, ".",
                               f"{len(checkable)} file(s) checked"))
            continue
        for rel, construct, message in hits:
            out.append(Finding(severity, "project", level, rule, rel,
                               f"{construct} — {message}"))
    return out, declared, implemented


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


USAGE = """rite-check — score a project against the Rite standard.

Usage:
  rite-check.py [PROJECT_DIR] [--force] [--exclude-scope=SCOPE]

  PROJECT_DIR             the project to check (default: the current directory)
  --force                 check a project that has no .rite.yaml marker, answering
                          "what would this score if it opted in?" It reads; it never writes.
  --exclude-scope=SCOPE   skip every test declaring that `scope:`, reporting each as NA
                          naming the exclusion. Note the `=`; the separate form is rejected,
                          because a bare value would be read as PROJECT_DIR.
  -h, --help              this message

Exit: 0 pass (or nothing to do) · 1 a RED finding · 2 a usage error
"""

# The flags this tool actually has. Anything else is a usage error rather than a silent no-op:
# until 2026-09-10 every unrecognised flag was discarded, so `--help` ran a full check and a
# typo'd `--exclude-scpoe=session` scored at FULL strength while the caller believed a scope had
# been excluded. A flag that looks accepted and does nothing is a silent wrong answer, which is
# the failure class this project exists to attack — here in its own entry point.
KNOWN_FLAGS = frozenset({"--force"})
KNOWN_FLAG_PREFIXES = ("--exclude-scope=",)
HELP_FLAGS = frozenset({"-h", "--help"})


def parse_flags(argv: list[str]) -> tuple[list[str], str | None]:
    """(unknown flags, help requested)."""
    unknown = []
    wants_help = False
    for a in argv:
        if not a.startswith("-") or a == "-":
            continue
        if a in HELP_FLAGS:
            wants_help = True
        elif a not in KNOWN_FLAGS and not a.startswith(KNOWN_FLAG_PREFIXES):
            unknown.append(a)
    return unknown, wants_help


def main(argv: list[str]) -> int:
    unknown, wants_help = parse_flags(argv[1:])
    if wants_help:
        print(USAGE, end="")
        return 0
    if unknown:
        plural = "s" if len(unknown) > 1 else ""
        print(f"rite-check: unknown option{plural}: {', '.join(unknown)}", file=sys.stderr)
        if any(a.startswith("--exclude-scope") for a in unknown):
            print("            did you mean --exclude-scope=SCOPE, with an '='?", file=sys.stderr)
        print("            run with --help for usage.", file=sys.stderr)
        return 2

    args = [a for a in argv[1:] if not a.startswith("-")]
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
