# The session protocol

> What happens at the start and end of a session, which half is mechanical and which needs judgement, and what check fails if you skip it.

**Version** `1.0.0` · **As of** `2026-09-08` · **Status** `draft`

_Generated from `spec/session-protocol.yaml`. Do not edit; run `spec/render-standard.py --protocol`._

claude-preflight is a session-START self-test with months of real use behind it. There has never been a session-END counterpart: the closing ritual — log, docs, memory, handoff — was three scattered sentences of prose and nothing that checked it. This is the half that was missing.

Transcripts are retained about four weeks on this machine (43 sessions, back to 2026-08-11) against ten months of LOG.md. Whatever is not distilled before a session ends is gone. The protocol exists because the raw record evaporates on the harness's schedule, not the user's.

## What forces the shape

**`session_end_has_no_turns`** — SessionEnd fires when Claude has no turns left.

It can copy files and stamp state. It CANNOT write a handoff, distil a LOG entry, or update docs. Every step needing judgement must run earlier, from a user-invoked command.

_Status: verified in the 2.1.263 binary._

**`prompts_versus_scripts`** — Skills, commands and agents are Markdown PROMPTS that Claude interprets. Hooks are JSON configuration. Scripts are the only executable component, invoked by hooks.

The judgement half is commands — no interpreter, no prerequisite, works anywhere Claude Code runs. The mechanical half is scripts and needs Python. The split the harness forced turns out to be the same split as prompt-versus-executable.

_Status: verified against code.claude.com/docs/en/plugins-reference, 2026-09-08._

_A happy accident, not a design. Recorded as such so nobody later mistakes it for cleverness and builds on it as though it were guaranteed._

## Phases

| phase | runs as | needs Python | degrades to |
|---|---|---|---|
| **Session start** | `SessionStart hook -> script` | yes | nothing — without Python the user simply gets no verdict; the session proceeds |
| **During the session** | `PostToolUse hook -> script, plus the agent's own discipline` | no | — |
| **Session end — the judgement half** | `/end command -> a Markdown prompt Claude interprets` | no | nothing — this half has no prerequisites and works on any machine Claude Code runs on |
| **Session end — the mechanical half** | `SessionEnd hook -> script` | yes | skipped, with the loss named at the next session start |

### Session start

**Must not.** block, prompt, or re-run anything with side effects

**Surface constraint.** Under entrypoint=claude-vscode only `additionalContext` reaches the session; systemMessage and showOutput do nothing. Design for additionalContext as the lowest common denominator and never assume a second channel.

- **`preflight_verdict`** — Run the configured checks and emit one verdict line, each finding tagged whose-side-to-fix.
  - _Why:_ Nobody else frames session health this way; it is the differentiated idea and it already works.
  - _Sides:_ `claude`, `project`, `machine`
- **`did_the_last_session_close`** — Compare HANDOFF.md `written:` against the newest LOG.md entry.
  - _Means:_ `written` older than the newest log entry means the session worked and then closed without touching the handoff. No stamp file is involved — two Tier 0 files that already exist.
- **`surface_the_handoff`** — Report the live handoff, or fail loudly on an expired or spent one, naming the file.
  - _Why:_ A spent handoff is worse than no handoff, because it is confidently wrong. No HANDOFF in the sampled corpus carried any expiry marker.

**Nag policy.** Report an unclosed previous session ONCE, then never again.

A warning that never clears is the gate that always fails, and a gate that always fails gets switched off within a week. Nagging once keeps the signal honest; nagging forever destroys it.

_Rejected: block until acknowledged — highest enforcement, highest chance the plugin is disabled on a busy morning._

### During the session

- **`mirror_memory`** — Mirror agent memory into the repo whenever a memory file changes.
  - _Why:_ A workspace rooted at the project cannot reach ~/.claude, which makes agent memory unauditable from the repo. One file, never a directory of them.
- **`log_continuously`** — Write LOG.md entries as events happen, not at the end.
  - _Why:_ Validated in practice on 2026-09-07: 85 entries written as the work happened. If the session dies before /end, everything up to that point survives. Distilling only at the end reproduces the evaporation problem the project exists to measure.
  - _Cost accepted:_ Logs are long. One evening produced 85 entries. That is the price of not losing the session.
- **`clock_per_entry`** — Read the machine clock for EVERY entry. Never extrapolate from an earlier reading.
  - _Why:_ Failed live on 2026-09-07: the clock was read at 22:11 and roughly thirty subsequent entries carried extrapolated times, some AHEAD of real time, discovered only when the clock was re-read at 00:02. An invented timestamp is indistinguishable from a real one afterwards.
  - _Check:_ no LOG entry may carry a timestamp later than the file's own mtime
  - _Tracked as:_ `c-log-timestamps-must-be-machine-read`

### Session end — the judgement half

**When.** user-invoked, while Claude still has turns

- **`distil_the_log`** — Review the continuous entries. Add what is missing. Where an entry turned out wrong, APPEND a dated correction — never rewrite it.
  - _Why:_ Continuous logging alone never reviews itself for gaps or for entries that were later disproved.
- **`update_what_changed`** — Bring the docs whose claims moved back to true.
  - _Do NOT:_ Touch as_of unless the file's claims were actually re-verified against the thing they describe.
  - _Covers:_ `ROADMAP current_state — it owns the project's stated state`, `ARCHITECTURE — declared must_be_current; rewrite in the same session the shape changes`, `DECISIONS — append any decision settled this session`, `CONCERNS — open, update or retire, using the declared three-way lifecycle`
- **`close_roadmap_items`** — Delete each finished near_term item and append one milestones entry naming its id.
  - _Do NOT:_ Mark an item done in place. The roadmap states the future only.
- **`handoff_decision`** — Record one of four outcomes in HANDOFF.md front matter as `session_end`.
  - _Why:_ The mandatory thing is the DECISION, not the prose. "Must have a handoff" is not testable; "must have recorded one of four outcomes" is. `none` is a real answer, written as genre: none — an explicit nothing beats an absence, because the two look identical from the next session's side except that one proves somebody decided.
  - _Freeze point:_ the handoff freezes here. Before this moment it is drafted freely; after it, a change means a NEW file.
  - _Outcomes:_ `written`, `updated`, `carried_forward`, `none`
- **`memory`** — Write or update what is worth remembering, and only that.
  - _Do NOT:_ Duplicate what the repo already records. Decisions belong in DECISIONS, not in memory. Memory is for what the repo cannot hold.

### Session end — the mechanical half

**Constraint.** No judgement. If a step needs a decision, it belongs in /end, not here.

- **`copy_plans`** — Copy plans from ~/.claude/plans into docs/PLAN-<date>-<slug>.md.
  - _Why blocked:_ Plan files carry harness-generated names with no project attribution (cheeky-seeking-clock.md). Recovering plan -> project needs mtime or session correlation. The only genuinely hard part of this half.
  - _Blocked by:_ `c-plan-attribution`
- **`mirror_memory_final`** — Run the memory mirror once more, so the repo-visible copy matches at close.

## Rulings that fixed the shape

_user, 2026-09-08. See d-session-protocol-shape._

- **`skipped_end`** — Nag once, then let it go.
- **`log_cadence`** — Continuous during the session, with a distilling pass at /end.
- **`minimum_session`** — None. The full ritual runs every session, regardless of size.
  - _How it stays bearable:_ The ritual is always RUN; its OUTPUT is proportional. A three-minute session has nothing to distil, no docs whose claims moved, no roadmap item to close, and a handoff of genre: none. Every step still executes and each one is a no-op with a recorded reason. It scales by content, not by exemption — which is why no threshold config exists.
  - _Dissent recorded:_ Claude recommended a measured threshold and argued that ceremony which does not scale down gets abandoned on a quick fix. Recorded so that IF the protocol is later skipped in practice, the cause is already written down rather than rediscovered.
- **`start_frame`** — Out of scope for now.
  - _Why:_ Preflight already covers session start. The end half is the actual gap and has never existed. Shipping the smaller spec targets it.
  - _If ever built:_ ai-collab-interaction/session-frame.yaml is the prior art — a blank template, unfilled since 2026-04-11. The one idea worth carrying is `trust_level` (discuss / plan / implement-and-review / just-do-it): declared collaboration INTENT, distinct from tool permission, which nothing else ships.

## Completion tests

A protocol with no completion test is not a protocol.

| test | level | checks | implementable today |
|---|---|---|---|
| `session_end_decision_recorded` | integrity | HANDOFF front matter carries `session_end` with one of the four outcomes. | True |
| `written_not_older_than_newest_log_entry` | integrity | HANDOFF `written:` is not older than the newest LOG.md entry. | True |
| `log_timestamps_not_in_the_future` | integrity | No LOG entry carries a timestamp later than the file's own mtime. | True |
| `nag_delivered_once` | integrity | An unclosed-session report is marked delivered and is not repeated. | True |
| `handoff_not_expired` | fresh | status: spent or a past `expires` date fails loudly, naming the file. | yes, as of 2026-09-08. `expires` is now always a DATE; a condition may accompany it in prose but is never the sole value. That was the only reason this test was unimplementable. |

- **`written_not_older_than_newest_log_entry`** — Distinguishes 'nobody thought about it' from 'someone decided none was needed'.
- **`log_timestamps_not_in_the_future`** — Catches extrapolated clocks. Would have caught the 2026-09-07 failure immediately.

## Honest limits

- THE START HALF RUNS; THE DURING HALF DOES NOT EXIST. SessionStart fires the hook, its verdict reaches the model's context, and the end half is reachable as /rite:end. But the `during` phase has no enforcement at all: mirror_memory, log_continuously and clock_per_entry are disciplines an agent must remember, which is the exact category this project exists to abolish. They wait on the PostToolUse watcher layer.
- EVERY IMPLEMENTED COMPLETION TEST IS AN END-OF-SESSION TEST. All five key off HANDOFF.md or off LOG.md's relationship to it. Nothing checks anything mid-session, so a session can run for hours doing everything wrong and the standard stays green until it closes. Found on 2026-09-10 when CI — which runs mid-session by nature — went red on written_not_older_than_newest_log_entry for a session that was simply still open.
- Four of the five tests are implementable with no revision history and no new artifact, which is deliberate: this protocol was designed so its own checks would not join the six already parked in c-unimplementable-tests.
- RESOLVED 2026-09-08. The nag-once mechanism needed somewhere to record that a report was delivered; HANDOFF front matter was the obvious place and the wrong one, because that file is write_once and freezes at session end. It lives in ${CLAUDE_PLUGIN_DATA} instead — the plugin's own storage, which ARCHITECTURE's never_mutate_claude_home already names as its one declared exception. Not a project artifact, so the inventory stays frozen at 13. Verified: the nag prose appears on the first run and not the second, while the checker's RED for the same condition correctly persists — a finding and a nag are different things.
