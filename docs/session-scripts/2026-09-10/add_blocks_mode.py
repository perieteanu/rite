import pathlib, sys
p = pathlib.Path("/home/perieteanu/projects/rite/spec/render-standard.py")
text = p.read_text(encoding="utf-8")
before = len(text.encode("utf-8"))

# 1 — the block machinery, inserted immediately before main()
anchor = "def main() -> int:"
if text.count(anchor) != 1:
    sys.exit(f"ABORT: main() anchor matched {text.count(anchor)} times")

machinery = '''# ── generated blocks ─────────────────────────────────────────────────────────
# A whole generated file cannot drift; a hand-written one that CONTAINS generated data can.
# README.md is prose a human owns with one table this spec owns, so the table is fenced by
# inert markers and refilled from the YAML. `--blocks --check` is the completion test, and it
# is the reason c-stage-table-duplicated-in-three-places could be retired rather than promised
# away. Targets are declared in `generated_blocks` in the YAML, never here — a path list that
# lives only in code is a hardcoded value with no human-visible home.
ROOT = HERE.parent


def _stage_table_rows(spec: dict) -> list[tuple[str, list[str]]]:
    """(stage, paths it adds) in stage order — exactly what rite-check.py gates on."""
    order = spec.get("stage_vocabulary", {}).get("values", [])
    by_stage: dict[str, list[str]] = {}
    for art in spec.get("artifacts", []):
        stage = art.get("required_from_stage")
        if stage:
            by_stage.setdefault(stage, []).append(_s(art.get("path")))
    return [(s, by_stage[s]) for s in order if s in by_stage]


def _stage_table(spec: dict, target: dict) -> str:
    rows = _stage_table_rows(spec)
    if not rows:
        raise ValueError("no artifact declares required_from_stage")
    style = target.get("style")
    notes = target.get("annotations") or {}

    if style == "md":
        out = ["| stage | what it adds |", "|---|---|"]
        for stage, paths in rows:
            out.append(f"| `{stage}` | " + ", ".join(f"`{p}`" for p in paths) + " |")
        return "\\n".join(out)

    if style == "yaml_comment":
        width = max(len(s) for s, _ in rows)
        out = []
        for i, (stage, paths) in enumerate(rows):
            lead = "" if i == 0 else "+ "
            line = f"#   {stage:<{width}}   {lead}" + ", ".join(paths)
            if stage in notes:
                line = f"{line}   {_s(notes[stage])}"
            out.append(line)
        return "\\n".join(out)

    raise ValueError(f"unknown block style {style!r}")


BLOCK_GENERATORS = {"stage-table": _stage_table}


def _block_targets(spec: dict):
    """(block id, target dict, open marker, close marker) for every declared target."""
    cfg = spec.get("generated_blocks") or {}
    markers = cfg.get("markers") or {}
    for block in cfg.get("blocks") or []:
        bid = _s(block.get("id"))
        for target in block.get("targets") or []:
            style = target.get("style")
            pair = markers.get(style)
            if not pair or len(pair) != 2:
                raise ValueError(f"{bid}: no marker pair declared for style {style!r}")
            yield bid, target, pair[0].replace("{id}", bid), pair[1]


def render_blocks(spec: dict, check: bool) -> int:
    problems: list[str] = []
    changed: list[str] = []
    seen = 0

    for bid, target, open_m, close_m in _block_targets(spec):
        rel = _s(target.get("path"))
        path = ROOT / rel
        seen += 1
        if not path.is_file():
            problems.append(f"{rel}: declared as a target for block '{bid}' but does not exist")
            continue

        text = path.read_text(encoding="utf-8")
        i = text.find(open_m)
        j = text.find(close_m, i + len(open_m)) if i != -1 else -1
        if i == -1 or j == -1:
            problems.append(
                f"{rel}: block '{bid}' has no {'opening' if i == -1 else 'closing'} marker. "
                f"Add {open_m!r} ... {close_m!r} around the generated region."
            )
            continue

        body = BLOCK_GENERATORS[bid](spec, target)
        rebuilt = text[: i + len(open_m)] + "\\n" + body + "\\n" + text[j:]
        if rebuilt == text:
            continue
        changed.append(rel)
        if check:
            diff = difflib.unified_diff(
                text.splitlines(keepends=True),
                rebuilt.splitlines(keepends=True),
                fromfile=f"{rel} (on disk)",
                tofile=f"{rel} (from {SPEC.name})",
                n=2,
            )
            sys.stdout.writelines(diff)
        else:
            path.write_text(rebuilt, encoding="utf-8", newline="\\n")

    if problems:
        for line in problems:
            print(f"FAIL  {line}")
        return 1

    if check:
        if changed:
            print(f"FAIL  {len(changed)} generated block(s) drifted from {SPEC.name}: "
                  + ", ".join(changed))
            print("\\nFix: spec/render-standard.py --blocks")
            return 1
        print(f"OK    {seen} generated block(s) match {SPEC.name}")
        return 0

    if changed:
        print(f"wrote {len(changed)} generated block(s): " + ", ".join(changed))
    else:
        print(f"OK    {seen} generated block(s) already match {SPEC.name}")
    return 0


'''

text = text.replace(anchor, machinery + anchor, 1)

# 2 — the flag
flag_anchor = '''    ap.add_argument(
        "--protocol",
        action="store_true",
        help="render the session protocol instead of the project standard",
    )
    args = ap.parse_args()
'''
if text.count(flag_anchor) != 1:
    sys.exit("ABORT: argparse anchor not found")
text = text.replace(flag_anchor, flag_anchor.rstrip("\n").replace(
    "    args = ap.parse_args()",
    '''    ap.add_argument(
        "--blocks",
        action="store_true",
        help="fill the generated blocks inside hand-written files (README, template)",
    )
    args = ap.parse_args()''') + "\n", 1)

# 3 — dispatch, before the SPEC.exists() guard's consumer
dispatch_anchor = """    rendered = render(spec)

    if not args.check:"""
if text.count(dispatch_anchor) != 1:
    sys.exit("ABORT: dispatch anchor not found")
text = text.replace(dispatch_anchor, """    if args.blocks:
        return render_blocks(spec, args.check)

    rendered = render(spec)

    if not args.check:""", 1)

p.write_text(text, encoding="utf-8", newline="\n")
print(f"render-standard.py: {before} -> {len(p.read_bytes())} bytes")
