import pathlib, sys
spec = pathlib.Path("spec/project-standard.yaml")
t = spec.read_text(encoding="utf-8")

pairs = [
 ('    path_pattern: "docs/PLAN-*.md"\n',
  '    path_pattern: "docs/PLAN-*.md"\n'
  '    canonical_name_pattern: "^docs/PLAN-\\\\d{4}-\\\\d{2}-\\\\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\\\\.md$"\n'),
 ('    path_pattern: "docs/session-scripts/*/*"\n',
  '    path_pattern: "docs/session-scripts/*/*"\n'
  '    canonical_name_pattern: "^docs/session-scripts/\\\\d{4}-\\\\d{2}-\\\\d{2}/[^/]+$"\n'),
]
for old, new in pairs:
    if t.count(old) != 1:
        sys.exit(f"ABORT: {old!r} matched {t.count(old)}")
    t = t.replace(old, new, 1)
spec.write_text(t, encoding="utf-8", newline="\n")

chk = pathlib.Path("scripts/rite-check.py")
c = chk.read_text(encoding="utf-8")
old_rule = '''CANONICAL_PLAN_NAME = re.compile(r"^PLAN-\\d{4}-\\d{2}-\\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\\.md$")


@rule("filename_matches_canonical")
def _filename_matches_canonical(ctx, art, test):
    """Every instance of a many-instance artifact is named the canonical way.

    Reachable only since path_pattern existed. Before that the artifact was matched literally
    against "docs/PLAN-YYYY-MM-DD-<slug>.md", so this rule had never once run against a real
    plan copy — c-pattern-paths-are-matched-literally.
    """
    pattern = art.get("path_pattern")
    if not pattern:
        return NA, "artifact declares no path_pattern"
    found = ctx.glob_matches(pattern)
    if not found:
        return NA, "no instances present"
    bad = [f for f in found if not CANONICAL_PLAN_NAME.match(f.rsplit("/", 1)[-1])]
    if bad:
        shape = art.get("structure", {}).get("canonical_name", "the canonical shape")
        return YELLOW, f"{len(bad)} of {len(found)} not named {shape}: " + ", ".join(bad)
    return GREEN, f"{len(found)} instance(s) canonically named"
'''
new_rule = '''@rule("filename_matches_canonical")
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
'''
if c.count(old_rule) != 1:
    sys.exit("ABORT: rule block not found")
chk.write_text(c.replace(old_rule, new_rule, 1), encoding="utf-8", newline="\n")
print("patched")
