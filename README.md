# Rite

Session discipline for Claude Code — enforced by checks that fail, not by conventions you
have to remember.

A session has two ends. At the start you need to know what state you are in and whose side a
problem is on. At the end you need what happened to survive the session that produced it.
Rite defines both, and defines what a project must carry so a cold agent can pick it up
without re-deriving it.

**Status:** `spec` — both halves are written, the project standard
([`spec/PROJECT-STANDARD.md`](spec/PROJECT-STANDARD.md)) and the session protocol
([`spec/SESSION-PROTOCOL.md`](spec/SESSION-PROTOCOL.md)); no plugin code yet.

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

## Not here yet

No plugin, no hooks, no slash commands, no packaging. The protocol is specified; nothing
implements it.
See [`docs/ROADMAP.yaml`](docs/ROADMAP.yaml).

## Credits

Developed by Perieteanu Costin in collaboration with Claude (Anthropic's Claude Code).

## Unofficial

Not affiliated with, endorsed by, or sponsored by Anthropic. It contains no Anthropic code
and makes no API calls; it reads files that Claude Code writes on your own machine.
