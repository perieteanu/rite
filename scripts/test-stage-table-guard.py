#!/usr/bin/env python3
"""Completion test: the stage->artifact mapping exists in ONE place, and copies cannot return.

WHY THIS EXISTS. On 2026-09-10 the mapping was hand-copied into README.md, template/.rite.yaml,
CLAUDE.md and docs/ROADMAP.yaml on the same day the mechanism it describes was built. Four
copies, three hand-maintained, introduced by the project whose entire thesis is that such
copies rot — c-stage-table-duplicated-in-three-places.

Two halves fix it, and only together:

  1. GENERATION removes the drift. README.md and template/.rite.yaml carry a `rite:generated`
     block filled from spec/project-standard.yaml, and `render-standard.py --blocks --check`
     fails when one drifts. That is the other gate, and it guards the copies that EXIST.

  2. THIS GUARD stops a FIFTH one appearing. Generation cannot: a new paragraph enumerating the
     stages in some other document is not drift from anything, it is a fresh copy, and
     --blocks --check would never look at it. Without this half, the fix lasts exactly until
     the next person explains the stages in prose — which is how the first four happened.

WHAT COUNTS AS A COPY. Not any mention of a stage: the word "shipped" appears throughout, and a
document explaining what stage gating IS must be free to say so. A copy is the DATA — three or
more stage names appearing near three or more artifact names, which is a mapping being restated
rather than a concept being described.

WHERE IT LOOKS, and every exclusion is a rule of this project rather than a convenience:

  scanned   README.md, CLAUDE.md, docs/*.md, template/*      live documents a reader acts on
  scanned   docs/ROADMAP.yaml UP TO `milestones:`            its rewrite-only zones only
  exempt    docs/ROADMAP.yaml FROM `milestones:`             append-only; a past entry stays as
                                                             written, and a guard that fails on
                                                             a file nobody may legally edit is a
                                                             gate that gets switched off
  exempt    LOG.md, docs/DECISIONS.yaml, docs/CONCERNS.yaml  append-only / history
  exempt    docs/PLAN-*.md                                   write-once archives
  exempt    spec/*                                           the authority itself, and the file
                                                             generated from it
  exempt    anything inside a `rite:generated` block         that is the generated copy
  exempt    anything inside a ``` fenced block               quoted OUTPUT, not a restatement

A KNOWN GAP, stated rather than hidden. The fenced-block exemption is not free: README.md
quotes a real checker run whose tail lists the same mapping ("not required at stage 'idea',
waiting on: spec README.md, CLAUDE.md ..."). That sample is a copy and it will rot the day an
artifact moves stage. It is exempt because the fix is a different machine — regenerating a
whole sample run needs a scratch project, not a table generator — and because a guard that
fires on a code fence would be switched off before it was fixed. See
c-readme-sample-output-is-a-copy.

Run:  python scripts/test-stage-table-guard.py
Exit: 0 pass · 1 fail
"""

from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import ritefs  # noqa: E402
import riteyaml  # noqa: E402

ritefs.use_utf8_stdio()

SPEC_PATH = ROOT / "spec" / "project-standard.yaml"

SCAN_GLOBS = ("README.md", "CLAUDE.md", "docs/*.md", "template/*", "template/.rite.yaml")

EXEMPT = {"docs/claude-memory.md"}

# docs/ROADMAP.yaml is MIXED: current_state is rewrite-only and must not carry a copy, while
# milestones below it is append-only and its entries stay exactly as they were written.
TRUNCATED = {"docs/ROADMAP.yaml": "milestones:"}

# A window this many lines wide. Wide enough for a four-row table or a wrapped sentence,
# narrow enough that unrelated prose pages apart cannot combine into a false positive.
WINDOW = 6
MIN_STAGES = 3
MIN_ARTIFACTS = 3

BLOCK_OPEN = re.compile(r"rite:generated\s+\S+")
BLOCK_CLOSE = re.compile(r"/rite:generated")
FENCE = re.compile(r"^\s*(```|~~~)")


def load_vocabulary() -> tuple[list[str], list[str]]:
    """(stage names, artifact names) read from the spec — never hardcoded here."""
    spec = riteyaml.load(SPEC_PATH.read_text(encoding="utf-8"), str(SPEC_PATH))
    stages = [str(s) for s in spec.get("stage_vocabulary", {}).get("values", [])]
    names: set[str] = set()
    for art in spec.get("artifacts", []):
        path = str(art.get("path") or "")
        if not path or "<" in path:
            continue
        leaf = path.rsplit("/", 1)[-1]
        names.add(leaf)
        # ARCHITECTURE.md is also written as bare "ARCHITECTURE" in prose, which is exactly the
        # abbreviation the old hand-written copies used. Catch the stem too.
        stem = leaf.rsplit(".", 1)[0]
        if stem.isupper() and len(stem) > 3:
            names.add(stem)
    return stages, sorted(names)


def strip_exempt_regions(lines: list[str]) -> list[str]:
    """Blank out generated blocks and fenced blocks, keeping line numbers intact."""
    out, in_block, in_fence = [], False, False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        if BLOCK_CLOSE.search(line):
            in_block = False
            out.append("")
            continue
        if BLOCK_OPEN.search(line):
            in_block = True
            out.append("")
            continue
        out.append("" if (in_block or in_fence) else line)
    return out


def scan_files() -> list[pathlib.Path]:
    seen: dict[str, pathlib.Path] = {}
    for pattern in SCAN_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            rel = path.relative_to(ROOT).as_posix()
            if not path.is_file() or rel in EXEMPT or rel.startswith("docs/PLAN-"):
                continue
            seen[rel] = path
    roadmap = ROOT / "docs" / "ROADMAP.yaml"
    if roadmap.is_file():
        seen["docs/ROADMAP.yaml"] = roadmap
    return [seen[k] for k in sorted(seen)]


def find_copies(lines: list[str], stages: list[str], artifacts: list[str]):
    """(first line of the window, stages found, artifacts found) for each restated mapping."""
    hits = []
    reported_until = 0
    for start in range(len(lines)):
        if start < reported_until:
            continue
        window = " ".join(lines[start:start + WINDOW])
        found_s = {s for s in stages if re.search(rf"(?<![\w-]){re.escape(s)}(?![\w-])", window)}
        found_a = {a for a in artifacts if a in window}
        if len(found_s) >= MIN_STAGES and len(found_a) >= MIN_ARTIFACTS:
            hits.append((start + 1, sorted(found_s), sorted(found_a)))
            reported_until = start + WINDOW
    return hits


def main() -> int:
    if not SPEC_PATH.is_file():
        print(f"FAIL  cannot read the authority: {SPEC_PATH}")
        return 1
    stages, artifacts = load_vocabulary()
    if not stages or not artifacts:
        print("FAIL  the spec declares no stage vocabulary or no artifact paths")
        return 1

    failures: list[str] = []
    scanned = 0

    for path in scan_files():
        rel = path.relative_to(ROOT).as_posix()
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        cut = TRUNCATED.get(rel)
        if cut:
            for i, line in enumerate(lines):
                if line.startswith(cut):
                    lines = lines[:i]
                    break
        scanned += 1
        for lineno, found_s, found_a in find_copies(
            strip_exempt_regions(lines), stages, artifacts
        ):
            failures.append(
                f"{rel}:{lineno}: restates the stage mapping outside a rite:generated block "
                f"— names stages {', '.join(found_s)} against {', '.join(found_a)}. "
                f"The mapping has one home: artifacts[].required_from_stage in "
                f"spec/project-standard.yaml. Describe the mechanism, or add a generated block."
            )

    if failures:
        print(f"FAIL  {len(failures)} restated copy of the stage mapping:"
              if len(failures) == 1 else
              f"FAIL  {len(failures)} restated copies of the stage mapping:")
        for f in failures:
            print(f"        {f}")
        print()
        print("      See generated_blocks in spec/project-standard.yaml, and")
        print("      spec/render-standard.py --blocks.")
        return 1

    print(f"PASS  {scanned} live document(s) restate no stage mapping; "
          f"{len(stages)} stage(s) and {len(artifacts)} artifact name(s) read from the spec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
