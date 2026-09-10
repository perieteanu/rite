import pathlib, sys
edits = [
 ("README.md",
  "Nine gates run on every push, across Linux, macOS and Windows. Two of them cannot run on a CI\n"
  "runner — the YAML parser's differential test needs PyYAML as an oracle, and the installed-copy\n"
  "test needs an installed plugin — so the runner reports **`10 of 13 gates ran`** and names the three\n"
  "it skipped rather than showing an unqualified green.\n",
  "Thirteen gates run on every push, across Linux, macOS and Windows. Three of them cannot run on\n"
  "a CI runner — the YAML parser's differential test needs PyYAML as an oracle, the installed-copy\n"
  "test needs an installed plugin, and the mirror-port parity test needs the original script Rite\n"
  "ported from — so the runner reports **`10 of 13 gates ran`** and names the three it skipped\n"
  "rather than showing an unqualified green.\n"),
 ("docs/ROADMAP.yaml",
  "  as its oracle and CI does not install it, and the installed-copy test needs an installed\n"
  "  plugin, which a runner never has. The runner names the two it skipped on every run, rather\n"
  "  than showing an unqualified green.\n",
  "  as its oracle and CI does not install it, the installed-copy test needs an installed plugin\n"
  "  which a runner never has, and the mirror-port parity test needs the original script rite was\n"
  "  ported from. That third one is TEMPORARY BY CONSTRUCTION: the original is Costin's fallback\n"
  "  while rite is on trial, and when he retires it the gate skips forever and must be deleted —\n"
  "  a gate that can no longer fail is not a gate. The runner names the three it skipped on every\n"
  "  run, rather than showing an unqualified green.\n"),
]
for rel, old, new in edits:
    p = pathlib.Path(rel)
    t = p.read_text(encoding="utf-8")
    if t.count(old) != 1:
        sys.exit(f"ABORT {rel}: matched {t.count(old)}")
    p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"{rel} updated")
