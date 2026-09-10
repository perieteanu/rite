import pathlib, sys
p = pathlib.Path("scripts/rite_preflight.py")
t = p.read_text(encoding="utf-8")

anchor = '''def run_checks(ctx, include_network):
    enabled = ctx.cfg.get("checks") or {}
    results = []
    for name, func, tier in REGISTRY:
        if enabled.get(name, True) is False:
            continue
        if tier == "full" and not include_network:
            continue
        try:
            results.append(func(ctx))
        except Exception as e:
            results.append(Result(name, "?", "YELLOW", f"check raised: {e}", ""))
    return results'''

new = '''# ── user-declared checks ─────────────────────────────────────────────────────
# THE CLAUSE THAT MAKES d-preflight-is-config-not-fork WORK: "plus checks too personal to
# publish." A check whose config carries a `command:` runs an external program instead of
# engine code, so a check that reads another project's files — or anything a user would never
# publish — needs no place in the engine at all.
#
#   checks:
#     tracker_registered:
#       command: ~/projects/project-tracker/bin/registered.py
#       side: project
#       timeout: 5
#
# The exit code IS the verdict. Anything else is YELLOW naming the check: a hook must not break
# the session it serves, and a check that vanished must never look like a check that passed.
EXIT_STATUS = {0: "GREEN", 1: "YELLOW", 2: "RED", 3: "NA"}


def run_command_check(name, spec, ctx):
    cmd = str(spec.get("command", "")).strip()
    side = spec.get("side", "project")
    if side not in ("claude", "project", "machine"):
        return Result(name, "?", "YELLOW", f"declares an unknown side {side!r}", "")
    if not cmd:
        return Result(name, side, "YELLOW", "declares no command", "")
    target = Path(cmd.split()[0]).expanduser()
    if not ritefs.exists_exactly(target):
        return Result(name, side, "YELLOW", f"command not found: {target}",
                      "Declared in checks.yaml but absent on this machine.")
    try:
        out = subprocess.run([str(target), *cmd.split()[1:]], capture_output=True, text=True,
                             timeout=float(spec.get("timeout", 10)), cwd=str(ctx.cwd),
                             encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return Result(name, side, "YELLOW", f"timed out after {spec.get('timeout', 10)}s", "")
    except OSError as e:
        return Result(name, side, "YELLOW", f"could not run: {e}", "")
    lines = [ln for ln in (out.stdout or "").splitlines() if ln.strip()]
    headline = lines[0] if lines else f"exit {out.returncode}"
    detail = "\\n".join(lines[1:])
    status = EXIT_STATUS.get(out.returncode)
    if status is None:
        return Result(name, side, "YELLOW",
                      f"exit {out.returncode} is not one of 0/1/2/3", headline)
    return Result(name, side, status, headline, detail)


def run_checks(ctx, include_network):
    enabled = ctx.cfg.get("checks") or {}
    results = []
    for name, func, tier in REGISTRY:
        if enabled.get(name, True) is False:
            continue
        if tier == "full" and not include_network:
            continue
        try:
            results.append(func(ctx))
        except Exception as e:
            results.append(Result(name, "?", "YELLOW", f"check raised: {e}", ""))
    # User-declared checks run after the built-ins, in declaration order. A name that collides
    # with a built-in is ignored rather than silently shadowing it — the engine's own checks are
    # not overridable, only switchable.
    built_in = {n for n, _, _ in REGISTRY}
    for name, spec in enabled.items():
        if not isinstance(spec, dict) or name in built_in:
            continue
        try:
            results.append(run_command_check(name, spec, ctx))
        except Exception as e:
            results.append(Result(name, "?", "YELLOW", f"check raised: {e}", ""))
    return results'''

if t.count(anchor) != 1:
    sys.exit("ABORT: run_checks not found")
p.write_text(t.replace(anchor, new, 1), encoding="utf-8", newline="\n")
print("command: checks added")
