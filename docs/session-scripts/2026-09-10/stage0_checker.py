import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/scripts/rite-check.py")
text = p.read_text(encoding="utf-8")
before = len(text.encode("utf-8"))

# 1 — a glob-matching helper beside exists_exactly, sharing its case-sensitivity guarantee
anchor = '''    def resolve(self, rel: str) -> tuple[str, str | None]:'''
helper = '''    def glob_matches(self, pattern: str) -> list[str]:
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

    def resolve(self, rel: str) -> tuple[str, str | None]:'''
if text.count(anchor) != 1:
    sys.exit("ABORT: resolve anchor not unique")
text = text.replace(anchor, helper, 1)

# 2 — presence honours path_pattern
old = '''        actual, note = ctx.resolve(art["path"])
        if note:
            art = dict(art, path=actual)
            findings.append(Finding(YELLOW, "project", "populated", "canonical_name",
                                    actual, note))
        present = ctx.exists_exactly(art["path"])
'''
new = '''        # AN ARTIFACT WITH MANY INSTANCES IS MATCHED BY GLOB, NOT BY NAME. plan_copy's `path`
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
'''
if text.count(old) != 1:
    sys.exit("ABORT: presence site not unique")
text = text.replace(old, new, 1)

p.write_text(text, encoding="utf-8", newline="\n")
print(f"rite-check.py: {before} -> {len(p.read_bytes())} bytes")
