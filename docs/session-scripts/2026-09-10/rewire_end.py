import pathlib, sys
p = pathlib.Path("scripts/rite_session_end.py")
t = p.read_text(encoding="utf-8")
before = len(t.encode("utf-8"))

start = t.index("def mirror_memory(root: Path) -> None:")
end = t.index("def main() -> int:")
new = '''def copy_everything(root: Path) -> None:
    """Mirror memory, copy plans, copy this session's scratchpad scripts.

    IN-PROCESS, not a subprocess. Until 2026-09-10 this shelled out to
    ~/.claude/scripts/claude-mirror-memory.py, which was the right call while that script was
    the only implementation — "a second implementation is drift, not robustness". It is no
    longer the only one: rite_copy.py is the port, so calling it directly removes both the
    subprocess and the dependency on a file outside the plugin.

    THE SCRIPTS ARE THE URGENT ONE. Plans and memory live under ~/.claude and survive; the
    scratchpad is under /tmp and does not survive a reboot. For those, late is the same as
    never, which is why this runs here — SessionEnd fires whether or not anyone remembers to
    type /rite:end.

    Silent and total: SessionEnd has no turns left, so nothing printed here reaches anyone, and
    one copier failing must not stop the next two.
    """
    for action in (rite_copy.mirror_memory, rite_copy.copy_plans, rite_copy.copy_scripts):
        try:
            action(root, False)
        except Exception:
            # A hook that raises is a hook that breaks the session it was meant to serve.
            continue


'''
t = t[:start] + new + t[end:]
t = t.replace("    mirror_memory(root)\n    copy_plans(root)\n", "    copy_everything(root)\n", 1)
t = t.replace("import json\nimport os\nimport subprocess\nimport sys",
              "import json\nimport os\nimport sys", 1)
t = t.replace("import ritefs  # noqa: E402", "import rite_copy  # noqa: E402\nimport ritefs  # noqa: E402", 1)
p.write_text(t, encoding="utf-8", newline="\n")
print(f"rite_session_end.py: {before} -> {len(p.read_bytes())}")
