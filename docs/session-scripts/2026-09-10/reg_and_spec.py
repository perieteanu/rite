import pathlib, sys

# 1 — the gate
g = pathlib.Path(".github/gates.yaml")
t = g.read_text(encoding="utf-8")
anchor = "  - id: mirror-port-parity"
new = '''  - id: preflight-port-parity
    command: [scripts/test-preflight-port-parity.py]
    what: "the ported session POST still agrees with preflight.py on status and side"
    skip_means: >
      ~/projects/claude-preflight/preflight.py is not on this machine. A CI runner never had it,
      and this is the END STATE: the original is Costin's fallback while Rite is on trial, and
      when he retires it this gate skips forever. DELETE IT THEN — a gate that can no longer
      fail is not a gate.

  - id: mirror-port-parity'''
if t.count(anchor) != 1:
    sys.exit("ABORT gate")
g.write_text(t.replace(anchor, new, 1), encoding="utf-8", newline="\n")
print("  ok  gate registered")

# 2 — the config contract, and the resolved deferral
s = pathlib.Path("spec/project-standard.yaml")
t = s.read_text(encoding="utf-8")
old = '''    - id: checks_yaml
      what: "Config driving the checks, inherited in shape from claude-preflight"
      status: "deferred — purpose not yet clear"
      note: >
        d-preflight-is-config-not-fork says preflight BECOMES this file, so it will exist. What
        it must contain for a stranger, versus for this machine, is unsettled.
'''
new = '''    - id: checks_yaml
      what: "Config driving the session POST, inherited in shape from claude-preflight"
      status: "RESOLVED 2026-09-10 — exists, and is NOT an artifact"
      note: >
        The deferral asked what it must contain for a stranger versus for this machine.
        Answered by building it. It lives at ${CLAUDE_PLUGIN_DATA}/checks.yaml — plugin storage,
        which never_mutate_claude_home names as its one declared exception, and where the
        nag-once mechanism already lives. It configures the MACHINE and the AGENT, not a
        repository, so a per-project copy would be the wrong shape and the inventory stays at
        14. template/checks.yaml is the documented default, carrying no machine-specific values.
        What is "for this machine" needs no answer from the standard after all: a check whose
        config carries a `command:` runs an external program, so anything too personal to
        publish lives in the user's config and never in the engine.
'''
if t.count(old) != 1:
    sys.exit("ABORT inventory")
t = t.replace(old, new, 1)
s.write_text(t, encoding="utf-8", newline="\n")
print("  ok  inventory deferral resolved")
