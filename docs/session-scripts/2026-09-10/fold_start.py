import pathlib, sys
p = pathlib.Path("scripts/rite_session_start.py")
t = p.read_text(encoding="utf-8")

# 1 — import the engine and the dedup
sub_old = "import ritefs  # noqa: E402"
if t.count(sub_old) != 1:
    sys.exit("ABORT: import anchor")
t = t.replace(sub_old,
              "import ritefs  # noqa: E402\nimport rite_preflight  # noqa: E402\n"
              "import ritededup  # noqa: E402", 1)

# 2 — the session POST goes FIRST, and runs whether or not the project opted in
old = '''    # Opt-in. Silent where not invited.
    if not ritefs.marker_present(root):
        emit(None)
        return 0

    parts: list[str] = []
'''
new = '''    # THE VS CODE EXTENSION HAS BEEN OBSERVED DISPATCHING ONE SessionStart TWICE, ~47ms apart
    # with the same session_id, so the verdict was injected twice. Rite's own hook was never
    # covered by the original guard, which protected only the two hooks in settings.json.
    # Fail-open: on any doubt it emits, because a duplicated line is far cheaper than a
    # silently missing verdict.
    window = 20
    try:
        window = int((rite_preflight.load_config().get("thresholds") or {})
                     .get("hook_dedup_window_s", 20))
    except Exception:
        pass
    if window and ritededup.already_emitted(payload, root, window,
                                            rite_preflight.STAMP_PATH):
        emit(None)
        return 0

    parts: list[str] = []

    # THE SESSION POST RUNS WHETHER OR NOT THE PROJECT OPTED IN, and comes first. It reports on
    # the machine and the agent — a disk filling up or a second interactive session is true
    # regardless of whether this directory carries a .rite.yaml. Only the PROJECT half below is
    # opt-in, which is what `participation` in the spec actually governs.
    post, _ = rite_preflight.local_verdict(root)
    if post:
        parts.append(post)

    # Opt-in. Silent where not invited — the project half only.
    if not ritefs.marker_present(root):
        emit("\\n\\n".join(parts) if parts else None)
        return 0
'''
if t.count(old) != 1:
    sys.exit("ABORT: opt-in block")
p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("session start folded")
