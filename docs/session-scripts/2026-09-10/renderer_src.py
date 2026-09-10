import pathlib, sys
p = pathlib.Path("spec/render-standard.py")
t = p.read_text(encoding="utf-8")

# 1 — generators for the gate blocks
anchor = 'BLOCK_GENERATORS = {"stage-table": _stage_table}'
gens = '''def _gate_data(data: dict) -> tuple[list, list]:
    gates = data.get("gates") or []
    return gates, [g for g in gates if g.get("skip_short")]


def _gate_counts(data: dict, target: dict) -> str:
    """The sentence README used to hand-maintain, and got wrong three times in one day.

    The SKIPPED count needs no second source: a gate that declares skip_short is a gate that
    can skip, so both numbers and the reasons all come from .github/gates.yaml.
    """
    gates, skippable = _gate_data(data)
    if not gates:
        raise ValueError("no gates declared")
    ran = len(gates) - len(skippable)
    clauses = ", ".join(
        f"`{_s(g.get('command', [''])[0]).rsplit('/', 1)[-1]}` ({_s(g['skip_short'])})"
        for g in skippable)
    if len(skippable) > 1:
        head, _, tail = clauses.rpartition(", ")
        clauses = f"{head} and {tail}"
    return (
        f"{len(gates)} gates run on every push, across Linux, macOS and Windows. "
        f"{len(skippable)} cannot run on a CI runner — {clauses} — so the runner reports "
        f"**`{ran} of {len(gates)} gates ran`** and names the {len(skippable)} it skipped "
        f"rather than showing an unqualified green."
    )


def _gate_list(data: dict, target: dict) -> str:
    gates, skippable = _gate_data(data)
    skips = {g["id"] for g in skippable}
    out = ["| gate | what it holds | on a runner |", "|---|---|---|"]
    for g in gates:
        gid = _s(g.get("id"))
        mark = "**skips**" if gid in skips else "runs"
        out.append(f"| `{gid}` | {_s(g.get('what'))} | {mark} |")
    return "\\n".join(out)


BLOCK_GENERATORS = {
    "stage-table": _stage_table,
    "gate-counts": _gate_counts,
    "gate-list": _gate_list,
}'''
if t.count(anchor) != 1:
    sys.exit("ABORT: generators anchor")
t = t.replace(anchor, gens, 1)

# 2 — a block may declare its own source file
old_iter = '''def _block_targets(spec: dict):
    """(block id, target dict, open marker, close marker) for every declared target."""
    cfg = spec.get("generated_blocks") or {}
    markers = cfg.get("markers") or {}
    for block in cfg.get("blocks") or []:
        bid = _s(block.get("id"))
        for target in block.get("targets") or []:'''
new_iter = '''_SOURCE_CACHE: dict[str, dict] = {}


def _block_source(block: dict, spec: dict) -> dict:
    """The data a block generates FROM.

    Defaults to the standard, which is what every block used until 2026-09-10. The gate blocks
    are fed from .github/gates.yaml instead, because that is the one home for the gate list and
    a generator reaching into the spec for it would recreate the copy it exists to remove.
    """
    rel = block.get("source_file")
    if not rel:
        return spec
    if rel not in _SOURCE_CACHE:
        path = ROOT / rel
        if not path.is_file():
            raise ValueError(f"source_file {rel} does not exist")
        _SOURCE_CACHE[rel] = riteyaml.load(path.read_text(encoding="utf-8"), str(path))
    return _SOURCE_CACHE[rel]


def _block_targets(spec: dict):
    """(block id, block, target dict, open marker, close marker) for every declared target."""
    cfg = spec.get("generated_blocks") or {}
    markers = cfg.get("markers") or {}
    for block in cfg.get("blocks") or []:
        bid = _s(block.get("id"))
        for target in block.get("targets") or []:'''
if t.count(old_iter) != 1:
    sys.exit("ABORT: _block_targets")
t = t.replace(old_iter, new_iter, 1)
t = t.replace("            yield bid, target, pair[0].replace(\"{id}\", bid), pair[1]",
              "            yield bid, block, target, pair[0].replace(\"{id}\", bid), pair[1]", 1)
t = t.replace("    for bid, target, open_m, close_m in _block_targets(spec):",
              "    for bid, block, target, open_m, close_m in _block_targets(spec):", 1)
t = t.replace("        body = BLOCK_GENERATORS[bid](spec, target)",
              "        body = BLOCK_GENERATORS[bid](_block_source(block, spec), target)", 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("renderer extended")
