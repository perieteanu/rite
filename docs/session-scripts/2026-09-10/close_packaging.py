import pathlib, sys
p = pathlib.Path("docs/ROADMAP.yaml")
t = p.read_text(encoding="utf-8")

old_item = '''  - id: plugin-packaging
    what: ".claude-plugin/marketplace.json at repo root, plugins/ layout, LICENSE, git init"
'''
if t.count(old_item) != 1:
    sys.exit("ABORT: plugin-packaging item")
t = t.replace(old_item, "", 1)

milestone = '''  - id: plugin-packaging
    what: ".claude-plugin/ manifests, LICENSE and a git repo — the plugin is installable and advertises itself"
    closed: "2026-09-10"
    log_ref: "10-09-2026"
    note: >
      CLOSED RETROSPECTIVELY, and that is the finding rather than the work. Every deliverable it
      named — marketplace.json at the repo root, plugin.json, LICENSE, git init — has existed
      since 2026-09-08, and the item sat in mid_term for two days while the project it described
      was published, ported and gated. Nobody looked.
      It was found by /rite:update's step 3, which asks whether anything actually finished, on
      the checkpoint command's first real run. That is the step most likely to be a no-op and it
      was not one — which is the argument for executing a step rather than reasoning about
      whether it applies.
      The "plugins/ layout" clause of the deliverable was never needed: Rite is one plugin at
      its own root advertising itself with `"source": "."`, and the plugins/ subdirectory form
      is for a marketplace listing OTHER repositories. Dropped as misconceived, not as skipped.

'''
anchor = "near_term:\n"
if t.count(anchor) != 1:
    sys.exit("ABORT: near_term anchor")
t = t.replace(anchor, milestone + anchor, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("plugin-packaging closed")
