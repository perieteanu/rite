# Rite

Session discipline for Claude Code — enforced by checks that fail, not by conventions you
have to remember.

A session has two ends. At the start you need to know what state you are in and whose side a
problem is on. At the end you need what happened to survive the session that produced it.
Rite defines both, and defines what a project must carry so a cold agent can pick it up
without re-deriving it.

**Status:** `build` — an installed, running Claude Code plugin. Both halves are specified
([`spec/PROJECT-STANDARD.md`](spec/PROJECT-STANDARD.md),
[`spec/SESSION-PROTOCOL.md`](spec/SESSION-PROTOCOL.md)), the checker runs, and the
start-of-session verdict reaches the model. Not published anywhere yet.

## Why

The raw record evaporates. Measured on the machine this was built on: four weeks of session
transcripts against ten months of `LOG.md`. Whatever is not distilled before a session ends
is gone — not archived, gone.

The usual answer is a rule: *"update the docs with current state."* That rule has no
completion test, so it fails quietly and you find out months later when a document confidently
describes a thing that has not been true since July. Rite's answer is that every artifact
declares a test, and the next session tells you which ones you skipped.

## What is here now

| path | what |
|---|---|
| [`spec/project-standard.yaml`](spec/project-standard.yaml) | The standard, machine form. Authoritative. |
| [`spec/PROJECT-STANDARD.md`](spec/PROJECT-STANDARD.md) | The same thing, readable. **Generated.** |
| [`spec/session-protocol.yaml`](spec/session-protocol.yaml) | The protocol, machine form. Authoritative. |
| [`spec/SESSION-PROTOCOL.md`](spec/SESSION-PROTOCOL.md) | The same thing, readable. **Generated.** |
| [`spec/render-standard.py`](spec/render-standard.py) | Generates both, and fails when either drifts. |
| [`scripts/rite-check.py`](scripts/rite-check.py) | The checker. Runs the standard's completion tests against a project. |
| [`scripts/riteyaml.py`](scripts/riteyaml.py) | Stdlib-only YAML subset parser. Refuses rather than guesses. |
| [`skills/`](skills/) | `/rite:log` `/rite:end` `/rite:handoff` `/rite:preflight` |
| [`hooks/`](hooks/) | `SessionStart` verdict, `SessionEnd` mechanical close. |

The spec is applied to itself on day one: the Markdown is generated from the YAML, and
`--check` fails if anyone edits it by hand. A standard that cannot catch its own drift has no
business asking that of anyone else.

```bash
python3 spec/render-standard.py                      # regenerate the standard
python3 spec/render-standard.py --check              # fail if it drifted
python3 spec/render-standard.py --protocol           # regenerate the protocol
python3 spec/render-standard.py --protocol --check   # fail if it drifted
```

## Prerequisites

**Python 3.** That is the whole list — there is nothing to `pip install`. On Windows the
command is `py` or `python`, not `python3`.

## What it costs you

Approximate, and worth checking rather than trusting — the numbers move whenever a skill's
description changes:

```
Always-on:  ~225 tok   added to every session, for four skill descriptions
On invoke:  ~0.9-1.2k  each time a skill actually runs
Hooks:      0          harness-only; they never enter the model's context
```

Reproduce it yourself with `claude plugin details rite`. That command is the honest answer;
the block above is a snapshot of it, and snapshots go stale.

## Not here yet

No published release — the namespace is claimed but the repository is private, so nobody but
its author has run this. CI runs the gates on every push across ubuntu, macos and windows —
though **without PyYAML**, so two of the eight gates skip there and the runner says so rather
than showing an unqualified green. There is no `template/` seed set, so a project adopting Rite
on day one still opens on a screen of RED. The `preflight.py` port and the continuous watcher
layer do not exist, and seven of the standard's declared tests are still unimplemented.
See [`docs/ROADMAP.yaml`](docs/ROADMAP.yaml).

<!-- rite:claims
# Every path below is checked on every run — see claims_match_filesystem in the standard.
# The prose above is prose; these are the parts of it a machine can falsify. When a sentence
# here says a thing does not exist, name it, and the check fails the day that stops being true.
absent:
  - scripts/preflight.py
  - scripts/status.json
present:
  - .github/workflows
  - scripts/rite-check.py
  - hooks/hooks.json
  - .claude-plugin/plugin.json
  - LICENSE
-->


## Credits

Developed by Perieteanu Costin in collaboration with Claude (Anthropic's Claude Code).

## Unofficial

Not affiliated with, endorsed by, or sponsored by Anthropic. It contains no Anthropic code
and makes no API calls; it reads files that Claude Code writes on your own machine.
