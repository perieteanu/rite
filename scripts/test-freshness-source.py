#!/usr/bin/env python3
"""Completion test: freshness is measured against RECORDED CHANGE, not file timestamps.

THE DEFECT THIS PINS, measured on 2026-09-11 and the reason c-source-is-filesystem-mtime was
opened at high severity. `newest_source_mtime` walked the filesystem and took mtimes, so on a
documents-only project EACH of these alone flipped both freshness rules from NA to YELLOW with no
document changed: a .gitignore, one untracked git-excluded PDF, one shell script. Backdating that
script's mtime silenced them again. The verdict followed the clock on a file rather than the
content of the tree — the "mtime theatre" CLAUDE.md names as the thing that would hollow these
tests out, arriving through the definition of SOURCE rather than of `as_of`.

WHY THIS TEST EXISTS AT ALL: the rule had none. Both freshness rules shipped, were declared in the
spec, ran on every project on this machine for days, and nothing anywhere asserted what they
measured against. That is how the defect survived being read several times.

THE CASES ARE THE FALSIFICATION, not a demonstration. Cases 1-2 are the concern's headline, case 4
is the one that proves mtime no longer decides anything, and cases 6-8 are the three ways the
answer can be UNKNOWABLE — each of which must say so in its own words rather than guess.

Run:  python scripts/test-freshness-source.py
Exit: 0 pass · 1 fail · 2 git is absent, so the fixtures cannot be built
"""

from __future__ import annotations

import datetime as dt
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import riterules  # noqa: E402
import ritefs  # noqa: E402
import riteyaml  # noqa: E402

ritefs.use_utf8_stdio()

if shutil.which("git") is None:
    print("SKIP  git is not on this machine, and every fixture here needs a repository.")
    print("      git is a CAPABILITY, not a prerequisite — see d-git-is-a-capability-not-a-"
          "prerequisite — so this gate skips rather than fails.")
    sys.exit(2)

SPEC = riteyaml.load((ROOT / "spec" / "project-standard.yaml").read_text(encoding="utf-8"),
                     "spec/project-standard.yaml")
TODAY = dt.date.today()
failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def git(root: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace",
    )


def write(root: pathlib.Path, rel: str, body: str) -> pathlib.Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def commit(root: pathlib.Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "-c", "user.email=fixture@example.invalid", "-c", "user.name=fixture",
        "commit", "-q", "-m", message)


# A documents-only project: documents, a marker, and a .gitignore. Nothing that any document in it
# could be describing.
DOCS_ONLY = {
    ".rite.yaml": "stage: idea\n",
    ".gitignore": "secrets/\nsources/\n",
    "LOG.md": "# LOG\n\n01-01-2026 09:00:00 | Thu | fixture | [note] Created\n",
    "docs/ROADMAP.yaml": 'as_of: "2026-01-01"\ncurrent_state: >\n  A fixture.\n',
}


def build(root: pathlib.Path, files: dict, *, init: bool = True, do_commit: bool = True) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for rel, body in files.items():
        write(root, rel, body)
    if init:
        git(root, "init", "-q", ".")
        if do_commit:
            commit(root, "fixture")


def activity(root: pathlib.Path, marker: dict | None = None):
    return riterules.newest_source_date(root, SPEC, marker)


with tempfile.TemporaryDirectory() as d:
    box = pathlib.Path(d)

    # 1. THE HEADLINE. A .gitignore and a marker are not source. Before this change, the presence
    #    of a .gitignore alone was enough to turn both freshness rules from NA to YELLOW — and
    #    every real git repository has one, which is why no real project ever reached the
    #    documents-only branch.
    a = box / "docs-only"
    build(a, DOCS_ONLY)
    got = activity(a)
    if got.date is not None:
        fail(f"a documents-only project reported a source date ({got.date}) — a .gitignore and a "
             f"marker are operational files, not the thing its documents describe")
    if "documents-only" not in got.reason:
        fail(f"the reason must say documents-only, got {got.reason!r}")

    # 2. An ignored file is not source either. git is asked what it knows, and it does not know
    #    about this PDF — which is the project's own statement that the file is not part of what
    #    it publishes about itself.
    write(a, "sources/manual.pdf", "not really a pdf")
    if activity(a).date is not None:
        fail("a git-ignored file counted as source")

    # 3. A committed script IS source, and the date is the COMMIT's, not the file's.
    b = box / "with-source"
    build(b, DOCS_ONLY)
    write(b, "tools/check.sh", "#!/usr/bin/env bash\necho ok\n")
    commit(b, "add a tool")
    got = activity(b)
    if got.date != TODAY:
        fail(f"a committed script should date source to its commit ({TODAY}), got {got.date}")
    if got.mode != "git":
        fail(f"a repository must be measured in git mode, got {got.mode!r}")

    # 4. THE CASE THAT PROVES THE FIX. Same content, mtime moved eight months into the past: the
    #    verdict must not budge. Under the old implementation this silenced both rules.
    (b / "tools" / "check.sh").touch()
    import os  # noqa: E402
    old = dt.datetime(2026, 1, 1).timestamp()
    os.utime(b / "tools" / "check.sh", (old, old))
    if activity(b).date != TODAY:
        fail("backdating a file's mtime changed the verdict — the measure is still following the "
             "filesystem clock rather than what was recorded")

    # 5. A dirty tree does not count as activity, and does not hide either: the ruling is that a
    #    document cannot be stale against an edit nothing has recorded, and the finding says so.
    write(b, "tools/check.sh", "#!/usr/bin/env bash\necho changed\n")
    got = activity(b)
    if got.date != TODAY:
        fail(f"an uncommitted edit changed the source date to {got.date}")
    if not got.dirty:
        fail("an uncommitted source change must be reported as dirty, not passed over in silence")

    # 6. A shallow clone still RETURNS a date, and that date is an artefact of the clone. This
    #    repo's own CI checks out shallow, so refusing it is not hypothetical.
    shallow = box / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{b}", str(shallow)],
                   capture_output=True, text=True, timeout=60,
                   encoding="utf-8", errors="replace")
    if (shallow / ".git").is_dir():
        got = activity(shallow)
        if got.date is not None:
            fail(f"a shallow clone reported {got.date} — commit dates there are an artefact of "
                 f"the clone, not of the project")
        if "shallow" not in got.reason:
            fail(f"the reason must name the shallow clone, got {got.reason!r}")
    else:
        fail("could not build a shallow clone fixture")

    # 7. A scaffolded project checked before its first commit. `git log` exits 128 here, which is
    #    NOT the same fact as documents-only and must not borrow its words.
    c = box / "no-commits"
    build(c, DOCS_ONLY, do_commit=False)
    got = activity(c)
    if got.date is not None:
        fail(f"a repository with no commits reported {got.date}")
    if "commit" not in got.reason:
        fail(f"the reason must say there are no commits yet, got {got.reason!r}")

    # 8. No repository at all: the filesystem is the only available answer, and the finding says
    #    which mode produced it. Six of ten sampled projects are not repositories, including the
    #    non-code ones d-noncode-first-class exists to serve.
    e = box / "no-git"
    build(e, DOCS_ONLY, init=False)
    script = write(e, "tools/check.sh", "#!/usr/bin/env bash\necho ok\n")
    os.utime(script, (old, old))
    got = activity(e)
    if got.mode != "mtime":
        fail(f"without a repository the mode must be mtime, got {got.mode!r}")
    if got.date != dt.date(2026, 1, 1):
        fail(f"mtime mode must use the file's own timestamp, got {got.date}")

    # 9. A project may declare that its own tooling is not what its documents describe — and the
    #    narrowing is reported, never silent. Same rule as a threshold override.
    got = activity(b, {"source_exclude": ["tools/"]})
    if got.date is not None:
        fail(f"a declared source_exclude was ignored — still reported {got.date}")
    write(b, ".rite.yaml", 'stage: idea\nsource_exclude:\n  - "tools/"\n')
    commit(b, "declare source_exclude")
    out = subprocess.run([sys.executable, str(HERE / "rite-check.py"), str(b)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if "source_exclude" not in (out.stdout + out.stderr):
        fail("the checker applied a declared source_exclude without reporting it")

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("PASS  source is recorded change: a .gitignore, an ignored file and a backdated mtime move\n"
      "      nothing; a commit does; a dirty tree is reported but does not count; and shallow,\n"
      "      no-commits and no-git each say what they cannot know in their own words.")
sys.exit(0)
