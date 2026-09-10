import json, pathlib, sys, collections

# 1 — hooks.json: declare the shell explicitly on every entry.
p = pathlib.Path("hooks/hooks.json")
d = json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
n = 0
for groups in d["hooks"].values():
    for g in groups:
        for h in g["hooks"]:
            if h.get("type") == "command" and "shell" not in h:
                items = list(h.items())
                items.insert(len(items) - 1 if "timeout" in h else len(items), ("shell", "bash"))
                g["hooks"][g["hooks"].index(h)] = collections.OrderedDict(items)
                n += 1
p.write_text(json.dumps(d, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
print(f"hooks.json: shell declared on {n} entries")

# 2 — spec: the coverage row that claimed a path no user can reach.
sp = pathlib.Path("spec/project-standard.yaml")
t = sp.read_text(encoding="utf-8")
old = '''        coverage:
          - "Linux -> sh -c -> the .sh shim"
          - "macOS -> sh -c -> the .sh shim"
          - "Windows with Git for Windows (the recommended setup) -> Git Bash -> the .sh shim"
          - "Windows without Git for Windows -> PowerShell -> the .ps1 shim"
'''
new = '''        coverage:
          - "Linux -> sh -c -> the .sh shim"
          - "macOS -> sh -c -> the .sh shim"
          - "Windows with Git for Windows -> Git Bash -> the .sh shim"
          - "Windows WITHOUT Git for Windows -> HOOKS DO NOT RUN. Git Bash is required."
        the_fourth_row_was_false_until_2026_09_10: >
          It read "Windows without Git for Windows -> PowerShell -> the .ps1 shim", which was
          the design INTENT and was never implemented. hooks.json names
          `bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh"` for every event and never references the
          .ps1, so on Windows without Git Bash the harness selects PowerShell, PowerShell looks
          for `bash`, and the hook fails. CI passed the .ps1 throughout by invoking it DIRECTLY,
          which is a green test over a code path production cannot reach — the most expensive
          kind of false assurance, and worse than the gap it was hiding.
        why_it_cannot_be_fixed_in_config: >
          Verified against the hooks reference 2026-09-10. A hook entry supports NO per-platform
          conditional — the docs say so outright — so one command string must serve every
          platform, and no string does: `bash X` fails under PowerShell, a bare `.sh` path
          fails under PowerShell, a bare `.ps1` path fails under sh. Exec form (`args`) skips
          the shell entirely and would solve it, except it needs one executable name that
          resolves everywhere, and that is the very problem the shim exists for — this machine
          has no `python` on PATH at all.
          Two entries with explicit `shell:` fields is the remaining idea. It is NOT taken:
          the docs do not say what a hook declaring an unavailable shell does, and building on
          undocumented behaviour is guessing. Revisit if that is ever specified.
        so_the_shell_is_declared_explicitly: >
          Every entry in hooks.json now sets `shell: bash`. It changes nothing where Git Bash
          exists, and where it does not it removes the silent fallback to a PowerShell that
          could only fail at our command string. The requirement becomes visible in the config
          rather than implied by it.
'''
if t.count(old) != 1:
    sys.exit("ABORT: coverage block")
sp.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("spec coverage corrected")
