import pathlib, sys
p = pathlib.Path("scripts/rite_preflight.py")
t = p.read_text(encoding="utf-8")
anchor = "def check_thinking_level(ctx):"
helper = '''def _vscode_state_blob():
    """Raw bytes of VS Code's global state DB, or None.

    Deliberately engine-free: python3 has sqlite3 built in, but the sibling reader in
    claude-persistent's extension cannot use one (node:sqlite is absent on Node 20), and both
    should agree. SQLite stores short text values verbatim in the page bytes, so a bounded
    regex finds them without opening the file as a database — read-only, no locking.

    LOST AND RESTORED during the port: it sat between two checks that were deliberately not
    ported, and cutting them by span took it too. The engine still RAN — the checker reported
    "check raised: name '_vscode_state_blob' is not defined" as a YELLOW, exactly as its
    per-check exception guard promises. A crash would have been louder and easier; a degraded
    check that keeps running is the failure mode worth having a guard for.
    """
    db = HOME / ".config" / "Code" / "User" / "globalStorage" / "state.vscdb"
    if not db.exists():
        return None
    try:
        return db.read_bytes().decode("latin1")
    except OSError:
        return None


def check_thinking_level(ctx):'''
if t.count(anchor) != 1:
    sys.exit("ABORT")
t = t.replace(anchor, helper, 1)
t = t.replace('    lines = [f"claude-preflight POST — {stamp}  ({ctx.cwd})",',
              '    lines = [f"rite preflight POST — {stamp}  ({ctx.cwd})",', 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("helper restored")
