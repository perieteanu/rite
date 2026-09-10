#!/usr/bin/env python3
"""rite_copy — bring into the project the things Claude writes OUTSIDE it.

Three sources, one spine, because ROADMAP said so and the exploration agreed: "Plans are the
identical problem with a different source dir. One tool, not two." A third joined them — the
helper scripts a session writes to its scratchpad, which is in /tmp and does not survive a
reboot, so the work that produced a commit becomes unreproducible the moment the machine
restarts.

  source                                              destination                  discipline
  ~/.claude/projects/<slug>/memory/*.md                docs/claude-memory.md        free_replace
  ~/.claude/plans/*.md                                 docs/PLAN-<ISO>-<slug>.md    write_once
  /tmp/claude-<uid>/<slug>/<session>/scratchpad/*      docs/session-scripts/<ISO>/  write_once

CARDINALITY FOLLOWS WRITE DISCIPLINE, and the spec already says why in
memory_mirror.structure.why_single_file: free_replace -> one file, write_once -> many. A mirror
is not an archive. Fanning a mirror out doubles the sync surface, because deletions must then be
reconciled and an orphaned mirror file is a lie that still reads as truth.

ATTRIBUTION, and why it stopped being the hard part. c-plan-attribution called this "the only
genuinely hard part" and proposed mtime correlation or content inspection. Neither is needed:
session transcripts live at ~/.claude/projects/<slug>/*.jsonl and contain the plan's absolute
path LITERALLY. Measured 2026-09-10: 13 of 13 plans on this machine attribute exactly. Scripts
need no attribution at all — their scratchpad path already contains the slug.

WHAT ATTRIBUTION ACTUALLY TELLS YOU, stated because it is narrower than it looks: the project
whose SESSION wrote the file, not the project the file is ABOUT. Proof is already in this repo.
docs/PLAN-2026-09-07-project-standard.md is the rite standard's founding plan and it was written
from a claude-persistent session, because rite did not exist yet. Transcript attribution says
claude-persistent; the human filed it under rite, and the human was right. So an existing copy
always wins over a fresh attribution, and this tool never moves or rewrites one.

IT REFUSES RATHER THAN GUESSES — the same rule riteyaml lives by. A plan matching no transcript
is reported unattributable and skipped. It is never placed by mtime proximity, because a
plausible wrong attribution is indistinguishable from a right one after the fact.

Run:  python scripts/rite_copy.py [--plans] [--memory] [--scripts] [--all] [--project P] [-n]
Exit: 0 always for the copy actions — this never blocks a session.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402

ritefs.use_utf8_stdio()

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
PLANS_DIR = CLAUDE_DIR / "plans"

# The home-root slug is the GLOBAL memory, never a project. Inherited from
# claude-mirror-memory.py, where it has been correct for months.
GLOBAL_HOME_SLUG = "-home-perieteanu"

MIRROR_SIGNATURE = "claude-mirror-memory/v1"
MIRROR_NAME = "claude-memory.md"
DOCS = "docs"
SCRIPTS_SUBDIR = "session-scripts"

# What counts as a session helper script. Deliberately narrow: today's scratchpad also held
# README.md.bak and a shipped-probe/ tree, and neither is a script.
SCRIPT_SUFFIXES = (".py", ".sh")

PLAN_PROVENANCE = re.compile(r"Copied from ~/\.claude/plans/(?P<name>[^\s]+\.md)")


# ── slug <-> path ────────────────────────────────────────────────────────────
# ONE DIRECTION IS TRUSTED. root -> slug is deterministic and is what governs every WRITE.
# slug -> root is not solved (claude_home_slug_derivation, severity: open) because the encoding
# is lossy: both "/" and "-" and "." become "-", so -home-x-public-html-api-perieteanu could
# decode to several real paths. It is used ONLY to name a project in a report, never to choose
# a directory to write into. That asymmetry is what makes the unsolved half harmless.

def encode_slug(path: Path | str) -> str:
    """Encode a path the way Claude Code names its project session dirs."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def slug_candidates(root: Path) -> list[str]:
    """Primary encoding first, then the underscore-preserving legacy variant.

    The encoding drifted between Claude Code versions and older folders kept "_"
    (-home-...-public_html-...). Carried over from claude-mirror-memory.py rather than
    rediscovered.
    """
    primary = encode_slug(root)
    legacy = re.sub(r"[^A-Za-z0-9_]", "-", str(root))
    return [primary] if legacy == primary else [primary, legacy]


def project_dir_for(root: Path) -> Path | None:
    for slug in slug_candidates(root):
        candidate = PROJECTS_DIR / slug
        if candidate.is_dir():
            return candidate
    return None


def memory_dir_for(root: Path) -> Path | None:
    pdir = project_dir_for(root)
    if pdir and (pdir / "memory").is_dir():
        return pdir / "memory"
    return None


# ── the attributor ───────────────────────────────────────────────────────────

def _transcripts() -> list[Path]:
    if not PROJECTS_DIR.is_dir():
        return []
    return sorted(PROJECTS_DIR.rglob("*.jsonl"))


def _slug_of(transcript: Path) -> str | None:
    """Walk up to the projects/<slug> level.

    A subagent transcript sits deeper — projects/<slug>/<uuid>/subagents/... — so the immediate
    parent is not the slug. Two of this machine's plans resolve only through this hop.
    """
    try:
        rel = transcript.relative_to(PROJECTS_DIR)
    except ValueError:
        return None
    return rel.parts[0] if rel.parts else None


def _authored_in(line: str, names: set[str]) -> set[str]:
    """Plan names this transcript line shows being WRITTEN, not merely mentioned.

    THE DISTINCTION IS THE WHOLE ATTRIBUTOR, and getting it wrong is not theoretical: the first
    version of this function matched any occurrence of "plans/<name>" anywhere in a transcript,
    and it mis-attributed five of thirteen plans. The contamination was self-inflicted — the
    session building this tool ran `ls ~/.claude/plans/`, so rite's own transcript came to
    mention every plan on the machine, and a naive index handed rite half of hwprivacy's work.
    The act of measuring changed what was measured.

    Authorship has exactly two shapes in a transcript, and both name the file as a TOOL INPUT
    rather than as text: a Write whose file_path is the plan, and an ExitPlanMode whose
    planFilePath is. A Bash command that merely lists the directory has neither.
    """
    found: set[str] = set()
    try:
        record = json.loads(line)
    except (ValueError, TypeError):
        return found
    message = record.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return found
    for item in content:
        if not isinstance(item, dict) or item.get("type") != "tool_use":
            continue
        payload = item.get("input")
        if not isinstance(payload, dict):
            continue
        if item.get("name") == "Write":
            target = payload.get("file_path")
        elif item.get("name") == "ExitPlanMode":
            target = payload.get("planFilePath")
        else:
            continue
        if not isinstance(target, str):
            continue
        leaf = target.rsplit("/", 1)[-1]
        if leaf in names and target.replace("\\", "/").endswith(f"plans/{leaf}"):
            found.add(leaf)
    return found


def build_attribution_index(names: set[str]) -> dict[str, set[str]]:
    """{plan filename: every slug whose session AUTHORED it}.

    A set rather than a slug, deliberately. Returning the first hit would silently pick a winner
    when two sessions both wrote the same path, and picking quietly is the failure this project
    exists to attack. The caller decides what a conflict means; this function only reports one.

    errors="replace" because a transcript is another process's output — the same rule every
    subprocess read in this repo follows. Lines are prefiltered on a cheap substring before
    json.loads, since almost none of them concern a plan.
    """
    index: dict[str, set[str]] = {}
    if not names:
        return index
    for transcript in _transcripts():
        slug = _slug_of(transcript)
        if not slug:
            continue
        try:
            text = transcript.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "plans/" not in text:
            continue
        for line in text.splitlines():
            if "plans/" not in line:
                continue
            for name in _authored_in(line, names):
                index.setdefault(name, set()).add(slug)
    return index


# ── reporting ────────────────────────────────────────────────────────────────

class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, action: str, what: str, detail: str = "") -> None:
        self.rows.append((action, what, detail))

    def render(self, title: str) -> int:
        print(f"rite — {title}")
        print()
        if not self.rows:
            print("  nothing to do")
            print()
            return 0
        width = max(len(a) for a, _, _ in self.rows)
        for action, what, detail in self.rows:
            line = f"  {action:<{width}}  {what}"
            print(f"{line} — {detail}" if detail else line)
        print()
        counts: dict[str, int] = {}
        for action, _, _ in self.rows:
            counts[action] = counts.get(action, 0) + 1
        print("  " + " · ".join(f"{n} {a}" for a, n in sorted(counts.items())))
        return 0


# ── plans ────────────────────────────────────────────────────────────────────

def _title_slug(text: str, fallback: str) -> str:
    """A kebab slug from the plan's first H1, which is what a human would have named it."""
    for line in text.splitlines():
        if line.startswith("# "):
            words = re.sub(r"[^a-z0-9\s-]", "", line[2:].strip().lower()).split()
            if words:
                return "-".join(words[:6])[:48].strip("-")
    return fallback


def _strip_provenance(text: str) -> str:
    """Drop a leading <!-- ... --> provenance header so a copy compares equal to its source."""
    stripped = text.lstrip()
    if stripped.startswith("<!--"):
        end = stripped.find("-->")
        if end != -1:
            return stripped[end + 3:].lstrip("\n")
    return text


def _existing_plan_bodies(docs: Path) -> dict[str, str]:
    """{sha256 of the copied body: copy filename}.

    KEYED ON CONTENT, NOT ON SOURCE NAME, and the reason is a property of the harness rather
    than a preference: ~/.claude/plans/<name>.md is REUSED. calm-tinkering-kahan.md held this
    repo's publishing plan in the morning and its copier plan in the afternoon. Keyed on the
    source filename, the second plan would have been skipped as "already copied" and lost — the
    quiet kind of data loss, where the tool reports success.

    Content also makes the check idempotent for copies that predate any provenance header, of
    which this repo has one.
    """
    out: dict[str, str] = {}
    if not docs.is_dir():
        return out
    for copy in sorted(docs.glob("PLAN-*.md")):
        try:
            body = _strip_provenance(copy.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        out[hashlib.sha256(body.encode("utf-8")).hexdigest()] = copy.name
    return out


def _plan_header(name: str, today: str) -> str:
    return (
        f"<!-- Copied from ~/.claude/plans/{name} on {today}.\n"
        "     Plans are written outside the project under harness-generated names carrying no\n"
        "     project attribution; they are lost when the session ends unless copied. Canonical\n"
        "     name per spec/project-standard.yaml artifact `plan_copy`. Copied by rite_copy.py,\n"
        "     which attributes a plan to the project whose SESSION wrote it. -->\n\n"
    )


def uncopied_plans(root: Path) -> list[str] | None:
    """Plans this project's session AUTHORED that have no copy in docs/.

    The read-only half of copy_plans, shared so the checker and the copier can never disagree
    about what "copied" means — two implementations of one predicate is the drift this project
    exists to attack. Returns None when there are no transcripts to attribute against, which is
    NA rather than a pass: nothing was checked.
    """
    if not _transcripts():
        return None
    docs = root / DOCS
    plans = sorted(PLANS_DIR.glob("*.md")) if PLANS_DIR.is_dir() else []
    index = build_attribution_index({q.name for q in plans})
    mine = set(slug_candidates(root))
    already = _existing_plan_bodies(docs)
    missing: list[str] = []
    for plan in plans:
        if not (index.get(plan.name) or set()) & mine:
            continue
        try:
            body = plan.read_text(encoding="utf-8")
        except OSError:
            continue
        if hashlib.sha256(body.encode("utf-8")).hexdigest() not in already:
            missing.append(plan.name)
    return missing


def copy_plans(root: Path, dry_run: bool) -> Report:
    report = Report()
    docs = root / DOCS
    if not PLANS_DIR.is_dir():
        report.add("skip", str(PLANS_DIR), "no plans directory on this machine")
        return report

    plans = sorted(PLANS_DIR.glob("*.md"))
    index = build_attribution_index({p.name for p in plans})
    mine = set(slug_candidates(root))
    already = _existing_plan_bodies(docs)
    today = dt.date.today().isoformat()

    for plan in plans:
        owners = index.get(plan.name) or set()
        if not owners:
            report.add("UNATTRIBUTED", plan.name,
                       "no session is recorded writing it — skipped, never guessed")
            continue
        if len(owners) > 1 and not (owners & mine):
            report.add("AMBIGUOUS", plan.name,
                       "authored in " + ", ".join(sorted(owners)) + " — not written")
            continue
        if not (owners & mine):
            report.add("elsewhere", plan.name,
                       f"belongs to {sorted(owners)[0]} — not written")
            continue
        body = plan.read_text(encoding="utf-8")
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if digest in already:
            report.add("have", plan.name, f"content already copied as {already[digest]}")
            continue

        date = dt.date.fromtimestamp(plan.stat().st_mtime).isoformat()
        dest = docs / f"PLAN-{date}-{_title_slug(body, plan.stem)}.md"
        if ritefs.exists_exactly(dest):
            report.add("have", plan.name, f"{dest.name} exists — write_once, never overwritten")
            continue
        if dry_run:
            report.add("would copy", plan.name, f"-> {dest.relative_to(root).as_posix()}")
            continue
        docs.mkdir(parents=True, exist_ok=True)
        dest.write_text(_plan_header(plan.name, today) + body, encoding="utf-8", newline="\n")
        report.add("copied", plan.name, f"-> {dest.relative_to(root).as_posix()}")
    return report


# ── session scripts ──────────────────────────────────────────────────────────

def scratchpad_dirs(root: Path) -> list[Path]:
    """Every scratchpad belonging to this project, newest session last.

    /tmp/claude-<uid>/<slug>/<session-uuid>/scratchpad. The slug is in the path, so these need
    no attribution — which is the whole reason scripts were cheap to add.
    """
    base = Path(os.environ.get("TMPDIR", "/tmp")) / f"claude-{os.getuid()}"
    out: list[Path] = []
    for slug in slug_candidates(root):
        holder = base / slug
        if not holder.is_dir():
            continue
        out.extend(sorted(p for p in holder.glob("*/scratchpad") if p.is_dir()))
    return out


def copy_scripts(root: Path, dry_run: bool) -> Report:
    report = Report()
    pads = scratchpad_dirs(root)
    if not pads:
        report.add("skip", "scratchpad", "none found for this project")
        return report

    for pad in pads:
        for src in sorted(pad.iterdir()):
            if not src.is_file() or src.suffix not in SCRIPT_SUFFIXES:
                continue
            date = dt.date.fromtimestamp(src.stat().st_mtime).isoformat()
            dest_dir = root / DOCS / SCRIPTS_SUBDIR / date
            dest = dest_dir / src.name
            if ritefs.exists_exactly(dest):
                report.add("have", src.name, "write_once — never overwritten")
                continue
            if dry_run:
                report.add("would copy", src.name, f"-> {dest.relative_to(root).as_posix()}")
                continue
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest.write_text(src.read_text(encoding="utf-8", errors="replace"),
                            encoding="utf-8", newline="\n")
            report.add("copied", src.name, f"-> {dest.relative_to(root).as_posix()}")
    return report


# ── memory mirror ────────────────────────────────────────────────────────────
# A PORT, not a rewrite. The output contract is kept byte-compatible with
# ~/.claude/scripts/claude-mirror-memory.py — same heading, same signature, same count line — so
# the existing docs/claude-memory.md does not churn and the two can run side by side while the
# port is proven. Dropped on the way over: the importlib load of claude-global-audit.py for
# registered_roots, which reaches into the portfolio registry that Rite does not own
# (d-project-tracker-stays-separate).

def memory_files(memdir: Path) -> list[Path]:
    """Durable memories, sorted. The MEMORY.md index is excluded — it is a table of contents."""
    return sorted(f for f in memdir.glob("*.md") if f.name != "MEMORY.md")


def read_type(path: Path) -> str:
    """metadata.type from front matter, falling back to the filename prefix."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unknown"
    m = re.search(r"^\s*type:\s*(\S+)\s*$", text, re.MULTILINE)
    if m:
        return m.group(1)
    return path.name.split("_", 1)[0] if "_" in path.name else "unknown"


def generate_mirror(slug: str, files: list[Path]) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Claude memory — project mirror",
        "",
        f"> Functional source of truth: `~/.claude/projects/{slug}/memory/`",
        "> Auto-generated by claude-mirror-memory — edits here do NOT propagate back.",
        f"> Last sync: {now}",
        f"> generator-signature: {MIRROR_SIGNATURE}",
        "",
        f"{len(files)} memories (MEMORY.md index excluded).",
        "",
    ]
    for f in files:
        try:
            body = f.read_text(encoding="utf-8", errors="replace").rstrip()
        except OSError as exc:
            body = f"(could not read: {exc})"
        lines += ["---", "", f"## {f.name} · type: {read_type(f)}", "", body, ""]
    return "\n".join(lines) + "\n"


MIRROR_STAMP = re.compile(r"^> Last sync: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})$", re.MULTILINE)

# The stamp has minute resolution, so a memory written in the same minute as the sync is not
# evidence of staleness. Only a file newer than the END of that minute counts.
STAMP_RESOLUTION = dt.timedelta(minutes=1)


def mirror_stamp(text: str) -> dt.datetime | None:
    m = MIRROR_STAMP.search(text)
    if not m:
        return None
    try:
        return dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def mirror_is_stale(root: Path, text: str, files: list[Path]) -> bool | None:
    """Is this mirror older than the memories it claims to mirror? None = cannot tell.

    SHARED WITH THE CHECKER on purpose, and the reason is a bug this had on its first run. The
    copier skipped rewriting whenever the CONTENT matched, ignoring the stamp; the checker
    judged staleness from the STAMP alone. So a mirror with a stale stamp and correct content
    was YELLOW forever, and the checker's own advice — "run rite_copy.py --memory" — did
    nothing. Two implementations of one predicate is the drift this project exists to attack,
    and it took under an hour to prove it on itself.
    """
    stamp = mirror_stamp(text)
    if stamp is None or not files:
        return None
    newest = max(f.stat().st_mtime for f in files)
    return newest > (stamp + STAMP_RESOLUTION).timestamp()


def mirror_memory(root: Path, dry_run: bool) -> Report:
    report = Report()
    memdir = memory_dir_for(root)
    if memdir is None:
        report.add("skip", "memory", "no memory folder for this project")
        return report
    slug = memdir.parent.name
    if slug == GLOBAL_HOME_SLUG:
        report.add("skip", slug, "the home-root slug is GLOBAL memory, never a project")
        return report

    files = memory_files(memdir)
    if not files:
        report.add("skip", "memory", "no memory files")
        return report

    target = root / DOCS / MIRROR_NAME
    text = generate_mirror(slug, files)

    if ritefs.exists_exactly(target):
        current = target.read_text(encoding="utf-8")
        if MIRROR_SIGNATURE not in current:
            report.add("REFUSED", target.name,
                       "exists without a generator signature — a hand-written file, not ours")
            return report
        # Compare everything but the clock: a timestamp differs on every run and would make
        # "unchanged" impossible to report, which is the same reason no generated file in this
        # repo carries one.
        strip = lambda s: MIRROR_STAMP.sub("", s)  # noqa: E731
        stale = mirror_is_stale(root, current, files)
        if strip(current) == strip(text) and stale is False:
            report.add("current", target.name, f"{len(files)} memories, unchanged")
            return report
        if strip(current) == strip(text):
            # Content matches but the stamp does not vouch for it. Rewriting refreshes the
            # stamp, which is the only thing mirror_not_stale can read.
            report.add("restamped", target.name, f"{len(files)} memories, sync stamp refreshed")
            if not dry_run:
                target.write_text(text, encoding="utf-8", newline="\n")
            return report
    if dry_run:
        report.add("would write", target.name, f"{len(files)} memories")
        return report
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    report.add("wrote", target.name, f"{len(files)} memories")
    return report


# ── cli ──────────────────────────────────────────────────────────────────────

def run_as_hook() -> int:
    """PostToolUse. Refresh the mirror only when a memory file was just written.

    WHY A MODE RATHER THAN JUST RUNNING --memory: a full refresh costs ~66ms, and PostToolUse
    fires on every Write and Edit. Paying that on every edit to catch the handful that touch a
    memory would be a tax on the whole session, and a hook that makes editing feel slow is a
    hook the user removes.

    It replaces the mid-session half of the global claude-mirror-memory hook, which is the only
    thing SessionEnd copying could not cover: end-of-session freshness leaves the mirror wrong
    for the length of the session, and the mirror exists to be READ from the workspace.

    ALWAYS EXITS 0. A hook that fails is a hook that breaks the session it was meant to serve,
    and this one is never worth a lost turn.
    """
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, TypeError):
        return 0
    tool = payload.get("tool_input")
    written = tool.get("file_path") if isinstance(tool, dict) else None
    if not isinstance(written, str):
        return 0
    # A memory file, not the MEMORY.md index — the index is a table of contents and the mirror
    # excludes it, so writing it changes nothing the mirror shows.
    normalised = written.replace("\\", "/")
    if "/memory/" not in normalised or normalised.endswith("/MEMORY.md"):
        return 0
    root = Path(payload.get("cwd") or os.getcwd()).resolve()
    if not ritefs.marker_present(root):
        return 0
    try:
        mirror_memory(root, False)
    except Exception:
        pass
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plans", action="store_true", help="copy attributable plans into the project")
    ap.add_argument("--memory", action="store_true", help="regenerate the memory mirror")
    ap.add_argument("--scripts", action="store_true", help="copy session helper scripts")
    ap.add_argument("--all", action="store_true", help="all three")
    ap.add_argument("--project", default=None, help="project root (default: cwd)")
    ap.add_argument("-n", "--dry-run", action="store_true", help="report, write nothing")
    ap.add_argument("--hook", action="store_true",
                    help="PostToolUse: refresh the mirror iff a memory file was written")
    args = ap.parse_args(argv[1:])

    if args.hook:
        return run_as_hook()

    root = Path(args.project).resolve() if args.project else Path.cwd()
    if not ritefs.marker_present(root):
        # Opt-in, and silent where not invited — the same participation rule the checker follows.
        return 0

    wanted = {
        "plans": args.plans or args.all,
        "memory": args.memory or args.all,
        "scripts": args.scripts or args.all,
    }
    if not any(wanted.values()):
        ap.print_help()
        return 2

    if wanted["plans"]:
        copy_plans(root, args.dry_run).render("plan copy")
    if wanted["scripts"]:
        copy_scripts(root, args.dry_run).render("session scripts")
    if wanted["memory"]:
        mirror_memory(root, args.dry_run).render("memory mirror")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
