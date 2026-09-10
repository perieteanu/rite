import json, pathlib, collections
p = pathlib.Path("hooks/hooks.json")
d = json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
d["description"] = ("rite — session protocol: verdict at start, mirror kept current during, "
                    "mechanical copy at end")
d["hooks"]["PostToolUse"] = [
    collections.OrderedDict([
        ("matcher", "Write|Edit|MultiEdit"),
        ("hooks", [collections.OrderedDict([
            ("type", "command"),
            ("command", 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/rite.sh" copy --hook'),
            ("timeout", 10),
        ])]),
    ])
]
p.write_text(json.dumps(d, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
print("PostToolUse registered")
