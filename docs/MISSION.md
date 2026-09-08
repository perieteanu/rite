---
schema_version: "1.0.0"
as_of: "2026-09-07"
status: current
---

# MISSION — rite

*Why this project exists. Read this first when reopening after a long gap.*

## Mission

Convert session discipline for Claude Code from a rule that must be remembered into a check
that fails. Define what a project must carry so a cold agent or a cold human can pick it up
without re-deriving it, define what happens at the start and end of a session, and ship both
as one Claude Code plugin.

Secondary:

- Make agent-side state auditable from the repo (memory, plans) instead of stranded in `~/.claude`.
- Give the ~12 months of accumulated practice a written, versioned form.
- Be publishable — a portfolio artifact that reads as engineering, not vibe-coding.

## The key insight

A rule with no completion test is not a rule. *"Update the docs with current state"* has been
standing instruction for a year and fails quietly because nothing checks it. Templates are
free and everyone has one; almost nobody ships the check that fails when you don't follow it.
**That check is the product.**

## The second insight

The raw record evaporates on the harness's schedule, not yours. Measured on this machine:
four weeks of session transcripts (43 sessions, back to 2026-08-11) against ten months of
`LOG.md`. Whatever is not distilled before a session ends is gone. That is not an argument for
the end-session protocol; it is the measurement of what happens without one.

## Motivation quotes

Verbatim, because paraphrase drifts:

- *"i want to leave a mark in the Claude/Code world"*
- *"code is the source of truth"*
- *"did WE spend enough time together to distill a new and eventually global spec?"*

## Constraints

- Cross-platform. Python and portable paths; no assumption of Linux, bash, or VS Code.
- No dependency on Costin's stack. preflight, project-tracker and the portfolio registry are
  optional enrichment, auto-detected; absent, the base layer still works.
- No Anthropic code, no API calls, no trademark use. Reads only files Claude Code writes locally.
- No hardcoded values. Anything tunable lives in a human-visible config file.
- The standard must pass a non-code project (a plumbing schematic) as readily as a Rust codebase.
- Never silently mutate `~/.claude`. Recommend and require consent; never write on the user's behalf.

## Non-goals

- A VS Code extension as the primary product. It is an optional viewer, one directory down.
- A status-bar monitor. Eight incumbents already occupy that lane and it is not the differentiator.
- Mass adoption. The goal is credibility: one clear idea, an honest README, negative findings left in.
- Portfolio scheduling, ranking, or "what should I do tonight" — that is project-tracker's job.
- Migrating existing projects to the canonical names. The standard defines the target; migration is opt-in.
- AI inference at check time. Every check must be reproducible by plain Python.

## Evidence base

~12.5 months (first prompt 2025-08-22) across 462+ sessions and 4864 prompts — a floor, since
the prompts DB was last ingested 2026-04-11. 1808 LOG entries across 50 projects, 230 ADRs,
249 memory files. Spanning Laravel, WordPress, PDF tooling, kernel-level hardware privacy,
Android, a plumbing schematic and an evacuation plan. The practice generalizes; it was never
written down.

## Honest limit

That corpus proves the practice was followed consistently. It does **not** prove the five-file
set is correct — nothing was tested against an alternative, no project deliberately went
without, and the drift found (8 naming schemes for EVOLUTION, 3 for HANDOFF, PLAN entirely
undeclared) shows the standard was imitated, never specified. This is a proven practice being
distilled, not a validated theory. Say it that way.
