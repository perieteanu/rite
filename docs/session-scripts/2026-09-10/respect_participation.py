import pathlib, sys
p = pathlib.Path("scripts/rite_session_start.py")
t = p.read_text(encoding="utf-8")
old = '''    parts: list[str] = []

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
new = '''    # OPT-IN COVERS THE SESSION POST TOO, and that was not the first answer here. The port
    # briefly ran the machine/agent checks regardless of the marker, reasoning that a disk
    # filling up is true whether or not this directory carries a .rite.yaml. The hook-shape
    # gate rejected it, and the gate was right: `participation` says Rite is silent where it
    # was not invited, full stop, and quietly carving out an exception is how a settled rule
    # becomes negotiable. Whether the POST should be exempt is a real question —
    # c-session-post-is-gated-by-participation — but it is a DECISION, not something to slip
    # into a port.
    if not ritefs.marker_present(root):
        emit(None)
        return 0

    parts: list[str] = []

    post, _ = rite_preflight.local_verdict(root)
    if post:
        parts.append(post)
'''
if t.count(old) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("participation respected")
