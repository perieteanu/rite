import pathlib, sys, datetime

# decision
d = pathlib.Path("docs/DECISIONS.yaml")
entry = '''
  - id: d-finish-the-half-built
    date: "2026-09-10"
    title: "Delete the unreachable, wire the unwired, implement the last rule"
    context: >
      Three pieces of the codebase were half-built and one was newly dead. Found by looking for
      remaining WORK rather than remaining FEATURES, which is a different question and turned out
      to be the more productive one.
    decision: >
      rite_preflight's --hook path is DELETED. required_any_of_sections is DECLARED on
      ARCHITECTURE and now honours section_aliases. deleted_ids_appear_in_milestones is
      IMPLEMENTED, taking the checker to 64 of 64 declared tests. watcher-cwd-changed is built.
    rationale:
      - >
        THE --hook PATH HAD NEVER RUN IN THIS CODEBASE. It came over with the port hours earlier;
        SessionStart routes through rite_session_start.py calling local_verdict(). Kept, it would
        be untested code presenting as supported, plus a second dedup implementation beside
        ritededup — the drift this project attacks, self-inflicted.
      - >
        required_any_of_sections WAS IMPLEMENTED AND INVOKED BY NOTHING. The spec declared its
        DATA under `structure:` and no artifact listed the rule under `tests:`. Wiring it found a
        second defect immediately: it compared against primary section names only, ignoring the
        `section_aliases` declared beside them, so a document doing exactly what the spec permits
        would have been reported as missing everything. Never noticed, because it had never run.
      - >
        deleted_ids_appear_in_milestones IS WHAT MAKES THE DELETION CONVENTION SAFE. Closing an
        item by deleting it is only sound if the item is promoted rather than erased, and until
        today that was a rule with no completion test. A DELETION IS NOT ALWAYS A CLOSURE: items
        legitimately move between lists, so an id leaving near_term is satisfied by a milestone
        OR by appearing elsewhere. Proved both ways on a throwaway git fixture.
      - >
        watcher-cwd-changed's value is not its code. Rite ASSUMES ONE PROJECT PER SESSION and had
        never said so; every artifact resolves from one root. CwdChanged has no matcher support
        and fires on every cd, so all the discrimination is the hook's — it speaks only on a move
        between two marked projects, once.
    also_settled: >
      The verdicts fixture's SECOND pinned literal was removed. "46" broke the moment a test was
      declared on a build-stage artifact. Both assertions now check the invariant they meant.
    chosen_by_user: true
    proposed_by: claude
'''
d.write_text(d.read_text(encoding="utf-8").rstrip("\n") + "\n" + entry, encoding="utf-8", newline="\n")

p = pathlib.Path("LOG.md")
entries = [
 ("fix", "DELETED rite_preflight's entire --hook path — emit_hook, read_payload, resolve_cwd, the flag and a second dedup, all unreachable. Nothing invoked it: SessionStart routes through rite_session_start.py calling local_verdict(). It came over with the port hours earlier. Kept, it would be untested code presenting as supported, plus a second dedup beside ritededup"),
 ("fix", "required_any_of_sections DECLARED at last — implemented since the checker was written and invoked by NOTHING, because the spec declared its data under `structure:` and no artifact listed the rule under `tests:`. Wiring it found a second defect immediately: it ignored the `section_aliases` declared beside it, so a document doing exactly what the spec permits would read as missing everything. Never noticed, because it had never run"),
 ("note", "It discriminates on first use: GREEN on rite, which has `## Shape`, and YELLOW on plumbing with the waiver named in the finding — exactly what required_any_of_waived_when predicted three days ago about a project whose top-level keys ARE the topology"),
 ("add", "deleted_ids_appear_in_milestones IMPLEMENTED — the last declared rule. 64 of 64, 0 NA, full coverage for the first time. It is what makes the deletion convention safe: closing by deleting is only sound if the item is promoted rather than erased, and until today that was a rule with no completion test"),
 ("note", "A DELETION IS NOT ALWAYS A CLOSURE, and the rule would be wrong without that. Items legitimately move between lists — ci-portability-matrix and two others went mid_term to near_term today — so an id leaving near_term is satisfied by a milestone OR by appearing elsewhere. Proved both ways on a throwaway git fixture: the erased id was named, the moved one was not"),
 ("add", "watcher-cwd-changed built, the second watcher. Its value is not the code: Rite ASSUMES ONE PROJECT PER SESSION and had never said so anywhere, while every artifact it writes resolves from one root. CwdChanged has NO matcher support and fires on every cd including into a subdirectory, so all the discrimination is the hook's own — it speaks once, only on a move between two marked projects"),
 ("fix", "Verified CwdChanged against the hooks reference before building rather than trusting the roadmap. It is real, carries the new cwd, has no matcher. The same lookup found Claude Code exposes THIRTY-THREE hook events where the locked findings named four — several unbuilt watchers were scoped against that short list. Corrected"),
 ("fix", "The verdicts fixture's SECOND pinned literal removed. '46' broke the moment a test was declared on a build-stage artifact. Both assertions now check the invariant they meant rather than a number that moves whenever the standard grows"),
]
lines = []
for kind, text in entries:
    now = datetime.datetime.now()
    dow = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][now.weekday()]
    lines.append(f"{now.strftime('%d-%m-%Y %H:%M:%S')} | {dow} | rite | [{kind}] {text}")
with p.open("a", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print(f"decision + {len(lines)} entries")
