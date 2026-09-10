import pathlib, sys

r = pathlib.Path("docs/ROADMAP.yaml")
t = r.read_text(encoding="utf-8")
start = t.index("  - id: watcher-cwd-changed")
end = t.index("  - id: status-json-as-flag-accumulator")
if "CwdChanged" not in t[start:end]:
    sys.exit("ABORT span")
t = t[:start] + t[end:]
milestone = '''  - id: watcher-cwd-changed
    what: "A mid-session move to a different project is reported once; every cd within one is silent"
    closed: "2026-09-10"
    log_ref: "10-09-2026"
    note: >
      The second watcher, and the cheap one the item promised. Its value was never the code —
      it is that Rite ASSUMES ONE PROJECT PER SESSION and had never said so anywhere. Every
      artifact it writes resolves from one root, so a session spanning two projects splits its
      record between them and nothing noticed.
      THE DISCRIMINATION IS ENTIRELY IN THE CODE, because CwdChanged has no matcher support and
      fires on every directory change including a cd into a subdirectory. Flagging all of them
      would be noise, and a noisy watcher is a disabled one. It speaks only on a move between
      two .rite.yaml projects, once per session.
      Verified against the hooks reference first rather than assumed: CwdChanged is real, its
      payload carries the new cwd, and it has no matcher. The same lookup found that Claude Code
      exposes THIRTY-THREE hook events where this project's locked findings named five.
      Only one project on this machine carries a marker, so in practice this will not fire until
      Rite is adopted somewhere else — which is itself the honest state of things.

'''
anchor = "near_term:\n"
r.write_text(t.replace(anchor, milestone + anchor, 1), encoding="utf-8", newline="\n")
print("  ok  roadmap closed")

c = pathlib.Path("CLAUDE.md")
t = c.read_text(encoding="utf-8")
old = '''- `SessionEnd` exists as a hook event (verified in the 2.1.263 binary alongside `Stop`,
  `PreCompact`, `SubagentStop`). **But it fires when there are no turns left**, so it can only
  do mechanical work. Judgement work must happen before, via a command.
'''
new = '''- **Claude Code exposes THIRTY-THREE hook events** — verified against the hooks reference
  2026-09-10, when this entry named four. Beyond the ones Rite uses there are `UserPromptSubmit`,
  `PostToolUseFailure`, `PostToolBatch`, `SubagentStart`, `TaskCreated`/`TaskCompleted`,
  `InstructionsLoaded`, `ConfigChange`, `DirectoryAdded`, `FileChanged`, `PostCompact`,
  `PreModelSwitch`/`PostModelSwitch` and more. **Read the reference before concluding an event
  does not exist** — several unbuilt watchers were scoped against a list of four.
- `SessionEnd` **fires when there are no turns left**, so it can only do mechanical work.
  Judgement work must happen before, via a command.
- `CwdChanged` has **no matcher support** and fires on every directory change, including a cd
  into a subdirectory. Any discrimination is the hook's own job.
'''
if t.count(old) != 1:
    sys.exit("ABORT locked findings")
c.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("  ok  locked findings corrected")
