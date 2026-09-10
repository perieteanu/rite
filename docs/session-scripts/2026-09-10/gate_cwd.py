import pathlib, sys
p = pathlib.Path("scripts/test-watch-discipline.py")
t = p.read_text(encoding="utf-8")
anchor = '''if failures:
    print(f"FAIL  {len(failures)} defect(s) in the write-discipline watcher:")'''
new = '''# ── the mid-session project switch ───────────────────────────────────────────
# CwdChanged has NO matcher support and fires on every directory change, so the discrimination
# is entirely in the code: a cd within one project must be silent, and only a move to a
# different project may speak. A watcher that flagged every cd would be disabled the same day.
import json  # noqa: E402
import tempfile  # noqa: E402

import rite_watch  # noqa: E402


def cwd_event(session: str, cwd: str, stamp: pathlib.Path) -> str:
    """Run the CwdChanged half against a temp stamp, returning whatever it printed."""
    import io
    import contextlib
    original = rite_watch.switch_stamp
    rite_watch.switch_stamp = lambda: stamp
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rite_watch.on_cwd_changed({"session_id": session, "hook_event_name": "CwdChanged",
                                       "cwd": cwd})
    finally:
        rite_watch.switch_stamp = original
    return buf.getvalue().strip()


with tempfile.TemporaryDirectory() as tmp:
    box = pathlib.Path(tmp)
    a, b = box / "project-a", box / "project-b"
    (a / "sub").mkdir(parents=True)
    b.mkdir()
    for d in (a, b):
        (d / ".rite.yaml").write_text("stage: idea\\n", encoding="utf-8", newline="\\n")
    stamp = box / "stamp.json"

    if cwd_event("s1", str(a), stamp):
        fail("spoke on the FIRST directory it saw — there is nothing to compare against yet")
    if cwd_event("s1", str(a / "sub"), stamp):
        fail("spoke on a cd WITHIN the same project — that is every other cd, and noise")

    spoke = cwd_event("s1", str(b), stamp)
    if not spoke:
        fail("stayed silent on a genuine move between two projects")
    else:
        try:
            ctx = json.loads(spoke)["hookSpecificOutput"]["additionalContext"]
        except (ValueError, KeyError):
            ctx = ""
            fail("the switch notice was not valid hookSpecificOutput JSON")
        if "project-a" not in ctx or "project-b" not in ctx:
            fail("the notice does not name both projects, so the reader cannot act on it")

    if cwd_event("s1", str(b), stamp):
        fail("spoke twice about the same switch — 'reported once' is what keeps it bearable")

    # A directory outside any Rite project is not ours to police.
    outside = box / "not-a-project"
    outside.mkdir()
    if cwd_event("s2", str(outside), stamp):
        fail("spoke about a directory carrying no .rite.yaml marker")

if failures:
    print(f"FAIL  {len(failures)} defect(s) in the write-discipline watcher:")'''
if t.count(anchor) != 1:
    sys.exit("ABORT")
t = t.replace(anchor, new, 1)
t = t.replace('print(f"PASS  future timestamps are caught and past ones are not; the {len(paths)} append-only "\n      f"artifacts are read from the spec, and MIXED files are not among them.")',
              'print(f"PASS  future timestamps are caught and past ones are not; the {len(paths)} append-only "\n'
              '      f"artifacts are read from the spec, MIXED files are not among them, and a project\\n"\n'
              '      f"      switch is reported once while every cd within a project is silent.")', 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("cwd cases added")
