import pathlib, sys
p = pathlib.Path("spec/project-standard.yaml")
t = p.read_text(encoding="utf-8")
before = len(t.encode("utf-8"))

# 1 — the 14th artifact, declared right after plan_copy since they share a shape
anchor = "  - id: concerns"
new_art = '''  - id: script_copy
    path: "docs/session-scripts/<ISO date>/<name>"
    path_pattern: "docs/session-scripts/*/*"
    write_discipline: write_once
    tier: 3
    layer: local
    answers: "How was this change actually made?"
    audience: both
    form: text
    structure:
      canonical_name: "session-scripts/<ISO date>/<original filename>"
      source: "/tmp/claude-<uid>/<slug>/<session-uuid>/scratchpad/*.py|*.sh"
      cardinality: many_files
      grouped_by_date: >
        Not flat beside the documents, unlike plan_copy. One session produced twenty helper
        scripts; a few sessions of that would bury docs/ under machinery and make the documents
        harder to find, which is the opposite of what docs/ is for.
      notes: >
        The throwaway scripts a session writes to do its own work — the ones that performed the
        edits behind a commit. They live in /tmp, so they do not survive a reboot: late is the
        same as never, which is why this runs from SessionEnd as well as /rite:end.
        Attribution is free, unlike plan_copy: the scratchpad path already contains the project
        slug, so nothing has to be inferred.
        Deliberately narrow about what counts — *.py and *.sh at the scratchpad root only. The
        session that built this had a README.md.bak and a shipped-probe/ tree in the same
        directory, and neither is a script.
    tests:
      - level: exists
        rule: optional
      - level: populated
        rule: filename_matches_canonical

  - id: concerns'''
if t.count(anchor) != 1:
    sys.exit("ABORT: concerns artifact anchor not unique")
t = t.replace(anchor, new_art, 1)

# 2 — the slug rule is half-solved now, and the half that matters is the solved one
old_rule = '''    - id: claude_home_slug_derivation
      severity: open
      rule: "Deriving a project slug from a path is platform-specific and is not yet solved."
      why: >
        Memory directories encode the project path as dashes
        (-home-perieteanu-projects-rite). On Windows that is a drive letter and backslashes.
        Unbuilt today; it lands in the port-mirror-memory work.
'''
new_rule = '''    - id: claude_home_slug_derivation
      severity: documentation
      rule: >
        Derive root -> slug and never slug -> root. The first is deterministic and governs every
        write; the second is lossy and may only name a project in a report.
      why: >
        Memory directories encode the project path with every non-alphanumeric character
        replaced by a dash (-home-perieteanu-projects-rite). On Windows that is a drive letter
        and backslashes, encoded the same way.
      resolved_2026_09_10: >
        This was `severity: open` and "not yet solved", deferred to the port-mirror-memory work
        — which is where it landed. The answer was not to solve the hard direction but to stop
        needing it. Encoding is LOSSY: "/", "-" and "." all become "-", so
        -home-x-public-html-api-perieteanu could decode to several real paths and any decoder
        would have to guess. rite_copy.py therefore derives root -> slug only, which is exact,
        and uses slug -> root for nothing but printing a project's name in a report. A wrong
        name in a report is a cosmetic defect; a wrong directory to write into is data loss.
        The asymmetry is what makes the unsolved half harmless, and it is why this is now
        severity: documentation rather than open.
      legacy_variant: >
        The encoding drifted between Claude Code versions: older folders preserved "_"
        (-home-...-public_html-...). Both spellings are tried, primary first.
'''
if t.count(old_rule) != 1:
    sys.exit("ABORT: slug rule not found")
t = t.replace(old_rule, new_rule, 1)

p.write_text(t, encoding="utf-8", newline="\n")
print(f"project-standard.yaml: {before} -> {len(p.read_bytes())} bytes")
