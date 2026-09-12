#!/usr/bin/env python3
"""Completion test for `legacy_layout` — the declared exception for projects predating docs/.

WHY IT EXISTS. Eleven projects were built before this standard and keep their documents in
docs-yaml/, in YAML where the standard names Markdown. Measured on one of them: 10 of its 27
YELLOW findings were that transition and NONE of them was fixable without migrating — 6
canonical_name, one per file forever, plus 4 Markdown section rules against YAML documents,
which no valid YAML can ever satisfy. Migration is opt-in by standing rule, so the project had
no way to say "this is what I have, and I will convert it."

WHAT THE RULE MUST DO, and each clause here is a case below:

  - suppress the LAYOUT findings — name and format — and nothing else;
  - report the declaration ONCE, never silently: overrides_are_never_silent applies to a
    declaration as much as to a threshold;
  - keep a format-shaped rule's PASS. The first implementation suppressed those rules wholesale
    and threw away three true greens on the measurement fixture. A document that satisfies the
    rule anyway is evidence, and an excuse must not consume it;
  - LAPSE when migrate_by passes, restoring every finding. A deadline that does nothing when it
    arrives is not a deadline;
  - hold with no date, and SAY it is undated, so an open-ended deferral cannot read like a dated
    one still in hand;
  - ignore a declaration whose directory is not there, so a marker left behind after a migration
    stops excusing a layout that no longer exists;
  - move what the COPIER writes, not just what the checker reads. A checker that accepts
    docs-yaml/ while the copier creates docs/ beside it is two tools disagreeing about one
    project.

Run:  python scripts/test-legacy-layout.py
Exit: 0 pass · 1 a failure
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CHECKER = HERE / "rite-check.py"
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import riterules  # noqa: E402
import riteyaml  # noqa: E402

ritefs.use_utf8_stdio()

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def run(root: pathlib.Path, force: bool = False) -> str:
    cmd = [sys.executable, str(CHECKER), str(root)] + (["--force"] if force else [])
    out = subprocess.run(cmd, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return out.stdout + out.stderr


def counts(output: str) -> dict[str, int]:
    for line in output.splitlines():
        if "checks ·" in line:
            parts = line.replace("·", " ").split()
            return {parts[i + 1]: int(parts[i])
                    for i, tok in enumerate(parts) if tok.isdigit()
                    and i + 1 < len(parts) and parts[i + 1] in
                    ("RED", "YELLOW", "NA", "GREEN")}
    return {}


# A documents-only project in the superseded layout: docs-yaml/, with MISSION and ARCHITECTURE
# as YAML where the standard names Markdown. Deliberately NOT a copy of a real project — a test
# that depends on another project's tree fails when that project is tidied.
MISSION = "schema_version: \"1.0.0\"\nstatus: current\nmission: \"a thing\"\n"
ARCH = "schema_version: \"1.0.0\"\nstatus: current\ncomponents:\n  a: \"one\"\n  b: \"two\"\n"
ROADMAP = "schema_version: \"1.0.0\"\nstatus: current\ncurrent_state: \"a state\"\n"


def build(tmp: pathlib.Path, marker: str | None, docs: str = "docs-yaml") -> None:
    (tmp / docs).mkdir(parents=True, exist_ok=True)
    (tmp / docs / "MISSION.yaml").write_text(MISSION, encoding="utf-8", newline="\n")
    (tmp / docs / "ARCHITECTURE.yaml").write_text(ARCH, encoding="utf-8", newline="\n")
    (tmp / docs / "ROADMAP.yaml").write_text(ROADMAP, encoding="utf-8", newline="\n")
    (tmp / "LOG.md").write_text("# log\n", encoding="utf-8", newline="\n")
    if marker is not None:
        (tmp / ".rite.yaml").write_text(marker, encoding="utf-8", newline="\n")


DECLARED = """legacy_layout:
  docs_dir: docs-yaml
  formats:
    mission: yaml
    architecture: yaml
  migrate_by: "{by}"
"""
UNDATED = """legacy_layout:
  docs_dir: docs-yaml
  formats:
    mission: yaml
    architecture: yaml
"""

# 1. The baseline, and 2. the declaration — measured against each other rather than against a
#    remembered number, because the absolute counts move whenever the standard gains a rule.
with tempfile.TemporaryDirectory() as d:
    base = pathlib.Path(d) / "plain"
    build(base, None)
    before = counts(run(base, force=True))

    with tempfile.TemporaryDirectory() as d2:
        dec = pathlib.Path(d2) / "declared"
        build(dec, DECLARED.format(by="2099-01-01"))
        out = run(dec)
        after = counts(out)

    if not before or not after:
        fail("could not read a verdict line from the checker")
    else:
        if after.get("YELLOW", 0) >= before.get("YELLOW", 0):
            fail(f"declaring changed nothing: YELLOW {before.get('YELLOW')} -> "
                 f"{after.get('YELLOW')}. The exception does not suppress.")
        if after.get("GREEN", 0) < before.get("GREEN", 0):
            fail(f"declaring destroyed {before.get('GREEN', 0) - after.get('GREEN', 0)} "
                 f"GREEN finding(s). A rule a document satisfies anyway must still be reported "
                 f"as passing — an excuse must not consume evidence.")
        if after.get("RED", 0) != before.get("RED", 0):
            fail("declaring a layout changed a RED. It excuses LAYOUT only — never content, "
                 "freshness, structure or integrity.")
    if "legacy_layout" not in out:
        fail("the declaration was not reported at all — a suppression nobody can see is a "
             "silent opt-out (overrides_are_never_silent).")
    if out.count("legacy_layout") != 1:
        fail(f"the declaration was reported {out.count('legacy_layout')} times; it must be "
             f"collapsed to exactly one line.")
    if "canonical_name" in out:
        fail("canonical_name still fired under a current declaration.")

# 3. Lapsed: every finding returns, plus the lapse itself.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d) / "lapsed"
    build(tmp, DECLARED.format(by="2000-01-01"))
    out = run(tmp)
    if "canonical_name" not in out:
        fail("a lapsed declaration still suppressed canonical_name. Every finding it covered "
             "must return in full.")
    lapse = [ln for ln in out.splitlines() if "legacy_layout" in ln]
    if not lapse or not lapse[0].strip().startswith("YELLOW"):
        fail("a lapsed declaration is not reported as YELLOW naming the missed date.")
    elif "2000-01-01" not in lapse[0]:
        fail(f"the lapse does not name the date that passed: {lapse[0].strip()}")

# 4. Undated: holds, and says so in those words.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d) / "undated"
    build(tmp, UNDATED)
    out = run(tmp)
    if "canonical_name" in out:
        fail("an undated declaration failed to suppress — it is permitted and must hold.")
    if "no migration date set" not in out:
        fail("an undated deferral does not say it is undated; it would read like a dated one "
             "still in hand.")

# 5. A declaration naming a directory that is not there excuses nothing.
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d) / "stale"
    build(tmp, DECLARED.format(by="2099-01-01"), docs="docs")
    out = run(tmp)
    if "legacy_layout" in out and "declared:" in out:
        fail("a declaration naming an absent directory was honoured. After a migration the "
             "leftover marker must stop excusing a layout that no longer exists.")

# 6. The copier moves too — the checker and the producer must agree about one project.
spec = riteyaml.load((ROOT / "spec" / "project-standard.yaml").read_text(encoding="utf-8"),
                     "spec")
legacy = {"legacy_layout": {"docs_dir": "docs-yaml"}}
for artifact in ("memory_mirror", "plan_copy", "script_copy"):
    canonical = riterules.artifact_path(spec, artifact)
    moved = riterules.artifact_path(spec, artifact, legacy)
    if canonical is None or moved is None:
        fail(f"{artifact}: the spec declares no path for it")
    elif not moved.startswith("docs-yaml/"):
        fail(f"{artifact}: the copier would still write to {moved!r} under a declared "
             f"docs-yaml/ layout — the checker would accept the file the copier never wrote.")
    elif riterules.canonical_docs_dir(spec) != "docs":
        fail("canonical_docs_dir followed the declaration; the 'canonical is ...' message "
             "would then name the legacy path as canonical.")

if failures:
    print()
    print(f"FAIL  {len(failures)} failure(s) in the legacy_layout contract.")
    sys.exit(1)

print("PASS  legacy_layout suppresses layout findings and nothing else, reports itself once, "
      "keeps passes, lapses on its date, holds undated, ignores a stale declaration, and "
      "moves what the copier writes.")
sys.exit(0)
