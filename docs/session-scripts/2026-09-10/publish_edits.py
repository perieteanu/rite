import pathlib, sys
ROOT = pathlib.Path("/home/perieteanu/projects/rite")

edits = [
# ── .rite.yaml: the stage advances, and the comment explaining `build` is replaced ──
("`build` is the honest value: the plugin runs and is installed, the namespace is claimed and\n"
 "# main is pushed, but the repository is PRIVATE and nothing is published. Declaring `shipped`\n"
 "# to turn the LICENSE check green would be lying to our own checker, which is the failure mode\n"
 "# this project exists to prevent. It advances in the same commit that makes the repo public —\n"
 "# d-stage-advances-when-the-repo-goes-public.\n"
 "stage: build",
 "`shipped` as of 2026-09-10, advanced in the SAME commit that made the repository public —\n"
 "# d-stage-advances-when-the-repo-goes-public. It said `build` until that moment, because\n"
 "# declaring `shipped` while private would have been lying to our own checker, which is the\n"
 "# failure mode this project exists to prevent.\n"
 "#\n"
 "# Note what this did NOT change, since the checklist expected otherwise: the LICENSE check was\n"
 "# already GREEN at `build`. required_from_stage gates whether an artifact is DEMANDED, not\n"
 "# whether it is CHECKED when present — LICENSE exists, so min_lines and no_provenance_header\n"
 "# always ran. The stage decides only whether a MISSING LICENSE is RED or NA.\n"
 "stage: shipped",
 ".rite.yaml"),

# ── README: the Status paragraph, which this commit falsifies ──
("**Status:** `build`. An installed, running Claude Code plugin, tested on Linux, macOS and\n"
 "Windows. **Not published yet** — the repository is private, so nobody but its author has run\n"
 "this. Treat the install instructions below as what will work, not as what you can do today.",
 "**Status:** `shipped`. An installed, running Claude Code plugin, tested on Linux, macOS and\n"
 "Windows, published 2026-09-10. It has been used daily by its author since 2026-09-07 and by\n"
 "nobody else, so treat the install instructions below as working but barely travelled.",
 "README.md"),

# ── CLAUDE.md: the "not built yet" list ──
("- **Nothing published.** `github.com/perieteanu/rite` is PRIVATE. It is no longer empty —\n"
 "  `main` was pushed on 2026-09-10 so that CI would have somewhere to run. A private push is\n"
 "  not publishing; `d-publish-main-in-full-no-export` governs the public one and it has not\n"
 "  happened.\n",
 "- **Published 2026-09-10.** `github.com/perieteanu/rite` is PUBLIC, `main` in full including\n"
 "  `LOG.md`, per `d-publish-main-in-full-no-export`. This bullet said \"Nothing published\" until\n"
 "  that commit. What is still true: **nobody but this machine has run Rite**, so every claim\n"
 "  about how it behaves elsewhere rests on CI, not on a user.\n",
 "CLAUDE.md"),

# ── ROADMAP current_state: two paragraphs ──
("  This is a git repo, and as of 2026-09-10 main is PUSHED to github.com/perieteanu/rite, which\n"
 "  is PRIVATE. A private push is not publishing: it exists so CI has somewhere to run, and\n"
 "  d-publish-main-in-full-no-export governs the public one, which has not happened. No one but\n"
 "  this machine has run Rite.\n"
 "  near_term is THE ORDERED PATH FROM PRIVATE TO PUBLIC and holds ONE item: publish-github. The\n"
 "  other three — ci-portability-matrix, setup-hook-scaffolding, readme-for-a-stranger — were all\n"
 "  queued and closed on 2026-09-10. Both of publish-github's blockers are settled: a project may\n"
 "  declare standard_version and a mismatch is YELLOW rather than honoured\n"
 "  (d-standard-version-declared-never-honoured), and the stage advances to `shipped` in the same\n"
 "  commit that flips visibility (d-stage-advances-when-the-repo-goes-public), which is exactly\n"
 "  when the LICENSE check should fire. Nothing technical is in the way; the remaining act is\n"
 "  Costin's, and the checklist for it is on the item.\n",
 "  RITE IS PUBLISHED. github.com/perieteanu/rite went PUBLIC on 2026-09-10, main in full with\n"
 "  LOG.md included, per d-publish-main-in-full-no-export. .rite.yaml advanced from `build` to\n"
 "  `shipped` in the same commit — d-stage-advances-when-the-repo-goes-public — which is the only\n"
 "  moment declaring `shipped` stops being a lie to our own checker.\n"
 "  ONE EXPECTATION OF THAT COMMIT WAS WRONG, and it is worth keeping because it was written down\n"
 "  first. The checklist said advancing the stage would turn the LICENSE check live and to\n"
 "  confirm it went GREEN not RED. It was ALREADY GREEN at `build`: required_from_stage gates\n"
 "  whether an artifact is DEMANDED, not whether it is CHECKED when present. The stage decides\n"
 "  only whether a MISSING LICENSE is RED or NA. Two documents asserted the NA and both were\n"
 "  wrong; the checker settled it against a stage: shipped copy of the tree.\n"
 "  STILL TRUE AND WORTH SAYING PLAINLY: no one but this machine has run Rite. Publishing changed\n"
 "  who CAN, not who HAS.\n"
 "  near_term is EMPTY. All four items of the path from private to public — ci-portability-matrix,\n"
 "  setup-hook-scaffolding, readme-for-a-stranger and publish-github — were queued and closed on\n"
 "  2026-09-10. That is a statement rather than an omission: the next move is a decision about\n"
 "  direction, not a queued task.\n",
 "docs/ROADMAP.yaml"),
]

for old, new, rel in edits:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {text.count(old)} times\n---\n{old[:120]}")
    b = len(text.encode("utf-8"))
    p.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print(f"{rel}: {b} -> {len(p.read_bytes())}")
