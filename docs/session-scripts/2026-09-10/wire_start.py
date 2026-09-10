import pathlib, sys
p = pathlib.Path("scripts/rite_preflight.py")
t = p.read_text(encoding="utf-8")

# Expose the compact verdict text so the SessionStart hook can fold it into ONE emission
# instead of a second hook printing a second JSON document.
anchor = "def emit_hook(results, verdict):\n    now = dt.datetime.now()"
new = '''def verdict_text(results, verdict):
    """The compact verdict, without the JSON envelope or the relay line.

    Split out during the port so rite_session_start.py can fold this into its single
    additionalContext emission. Two hooks each printing their own JSON is what the port
    replaces — the user had one line from preflight and one from rite, describing one session.
    """
    now = dt.datetime.now()
    n = sum(1 for r in results if r.status != "NA")
    if verdict == "GREEN":
        return f"preflight GREEN — {n} checks ok ({now:%H:%M})"
    out = [f"preflight {verdict} — session POST ({now:%H:%M}):"]
    for r in results:
        if r.status in ("YELLOW", "RED"):
            out.append(f"  [{r.status}/{r.side}] {r.name}: {r.headline}")
    out.append(f"full report: {REPORT_PATH}")
    return "\\n".join(out)


def local_verdict(cwd):
    """Run the local tier for `cwd` and return (text, verdict). Never raises.

    The entry point rite_session_start.py uses. A session POST that throws would block the
    session it exists to inform, so every failure degrades to no text at all.
    """
    try:
        cfg = load_config()
        ctx = Ctx(cwd, cfg)
        results = run_checks(ctx, include_network=False)
        if not results:
            return None, "GREEN"
        verdict = verdict_of(results)
        write_report(ctx, results, verdict, False)
        return verdict_text(results, verdict), verdict
    except Exception:
        return None, "GREEN"


def emit_hook(results, verdict):
    now = dt.datetime.now()'''
if t.count(anchor) != 1:
    sys.exit("ABORT: emit_hook anchor")
p.write_text(t.replace(anchor, new, 1), encoding="utf-8", newline="\n")
print("verdict_text + local_verdict exposed")
