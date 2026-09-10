import pathlib, sys
p = pathlib.Path(".github/gates.yaml")
t = p.read_text(encoding="utf-8")
adds = [
 ("  - id: riteyaml\n    command: [scripts/test-riteyaml.py]\n    what: \"riteyaml parses this project's YAML identically to PyYAML\"\n",
  "  - id: riteyaml\n    command: [scripts/test-riteyaml.py]\n    what: \"riteyaml parses this project's YAML identically to PyYAML\"\n    skip_short: \"PyYAML is its oracle and CI does not install it\"\n"),
 ("  - id: installed-copy\n    command: [scripts/test-installed-current.py]\n    what: \"the installed plugin matches this working tree, by version and by content\"\n",
  "  - id: installed-copy\n    command: [scripts/test-installed-current.py]\n    what: \"the installed plugin matches this working tree, by version and by content\"\n    skip_short: \"a runner has no installed plugin\"\n"),
 ("  - id: mirror-port-parity\n    command: [scripts/test-mirror-port-parity.py]\n    what: \"rite's memory mirror still renders identically to the script it ported\"\n",
  "  - id: mirror-port-parity\n    command: [scripts/test-mirror-port-parity.py]\n    what: \"rite's memory mirror still renders identically to the script it ported\"\n    skip_short: \"a runner has no copy of the script Rite ported from\"\n"),
]
for old, new in adds:
    if t.count(old) != 1:
        sys.exit(f"ABORT: matched {t.count(old)}\n{old[:60]}")
    t = t.replace(old, new, 1)
# document the new field where the file explains itself
t = t.replace(
 "# EXIT CODES are a contract shared by every gate: 0 pass, 1 fail, 2 skip. A gate that can skip\n# declares `skip_means`, and the runner refuses to fold a skip into green.",
 "# EXIT CODES are a contract shared by every gate: 0 pass, 1 fail, 2 skip. A gate that can skip\n"
 "# declares `skip_means`, and the runner refuses to fold a skip into green.\n"
 "#\n"
 "# `skip_short` is the same fact in one clause, for the sentence README and ARCHITECTURE\n"
 "# GENERATE from this file. Declaring it here is the point: the gate count was hand-copied into\n"
 "# four documents and went 9 -> 11 -> 12 -> 13 in a single day, falsifying four or five\n"
 "# sentences each time (c-gate-count-restated-in-prose). A gate that declares skip_means is a\n"
 "# gate that can skip, so the skipped COUNT needs no second source either.", 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("gates.yaml: skip_short declared")
