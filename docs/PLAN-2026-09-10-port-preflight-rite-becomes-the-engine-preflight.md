<!-- Copied from ~/.claude/plans/calm-tinkering-kahan.md on 2026-09-10.
     Plans are written outside the project under harness-generated names carrying no
     project attribution; they are lost when the session ends unless copied. Canonical
     name per spec/project-standard.yaml artifact `plan_copy`. Copied by rite_copy.py,
     which attributes a plan to the project whose SESSION wrote it. -->

# port-preflight — Rite becomes the engine, preflight becomes a config

## Context

`d-preflight-is-config-not-fork` (2026-09-07) settled the shape and has waited three days:
*"Rite is the upstream engine. Costin's preflight shrinks to his own checks.yaml plus checks too
personal to publish."* This builds it. It is the last large piece of the stated product, and it
is what makes "retire the old scripts" possible rather than aspirational.

Four findings from exploration, each of which changes the work:

1. **`riteyaml` already parses `checks.yaml` identically to PyYAML.** Verified against the real
   file, with PyYAML as oracle. `preflight.py` does `import yaml; yaml.safe_load` — the port
   swaps one import and needs no parser work. This was the only plausible blocker and it is gone.
2. **The generalisation is genuinely mostly done.** 748 lines contain **3** machine-specific
   literals; the rest is already driven by `checks.yaml` — thresholds, `disk_mounts`, `caveats`,
   `remotes`. The decision's claim that this happened "accidentally" holds up.
3. **Two checks are superseded, not portable.** `mirror_drift` compares mtimes — mtime theatre
   by this project's own name for it — where Rite's `mirror_not_stale` reads the sync stamp
   through a predicate shared with the copier. `last_log_age` duplicates
   `newest_entry_within_days_of_activity`. Porting either would be two implementations of one
   predicate, which is the drift the mirror parity gate exists to catch.
4. **Rite has no dedup.** `hookdedup.py` guards the two hooks registered in `settings.json`;
   Rite's own `SessionStart` was never covered. Whether it actually double-fires on 2.1.266 is
   **unverified** — see Verification, and do not assume either way.

The vocabulary already matches: preflight's `Result(name, side, status, headline, detail)` and
sides `claude|project|machine` are what Rite's spec inherited in `verdicts`.

---

## Stage 0 — Where `checks.yaml` lives, and why it is not the 15th artifact

- **`${CLAUDE_PLUGIN_DATA}/checks.yaml`**, user-level, not per-project. It configures the
  machine and the agent, not a repository, so a per-project copy would be the wrong shape.
- **The artifact inventory stays at 14.** This is plugin storage, not a project artifact — the
  same reasoning and the same location that the nag-once mechanism already uses, which
  `ARCHITECTURE`'s `never_mutate_claude_home` names as its one declared exception.
- The inventory currently lists `checks_yaml` as *"deferred — purpose not yet clear"*. **That
  deferral is resolved by this work**: update the entry to say where it lives and that it is not
  an artifact, rather than deleting it.
- Declare the file's contract in `spec/project-standard.yaml` under a new `checks_config:` key —
  thresholds, per-check toggles, `disk_mounts`, `caveats`, `remotes`, and the `command:` form.
- **Ship a documented default** in `template/checks.yaml` so a stranger has a starting point,
  carrying no machine-specific values.

## Stage 1 — The engine

New `scripts/rite_preflight.py`. Port `preflight.py`'s spine, reusing what exists rather than
re-deriving it:

- `riteyaml.load` for the config; `ritefs.use_utf8_stdio()` before printing; every read of
  another process names `encoding="utf-8"` **and** `errors="replace"` — the AST gate enforces
  both and will fail the build if missed.
- Keep `Result`, `ORDER`, `GLYPH`, `verdict_of` and the `REGISTRY` shape as they are. They work,
  and the vocabulary is already Rite's.
- Keep the two tiers: `local` runs automatically, `full` (network) only on explicit request.
  **`SessionStart` must never touch the network** — the spec's `never_blocks_a_session` and the
  start phase's `must_not` both already forbid it.

## Stage 2 — The eleven publishable checks

Port unchanged in behaviour, with all machine-specific data coming from config:

`parallel_claude`, `context_files`, `settings_valid`, `git_status`, `disk` (mounts from config),
`thinking_level`, `context_window`, `caveats` (content from config), and the `full`-tier
`mcp_reachable`, `google_auth`, `remote_reachable` (probes from config).

**Do not port `mirror_drift` or `last_log_age`.** Rite's own checks supersede both. Record that
in the spec beside the ported list so a future session does not "restore" them as omissions.

## Stage 3 — `command:` checks, the extension point

The clause that makes the whole decision work — *"plus checks too personal to publish."*

```yaml
checks:
  tracker_registered:
    command: ~/projects/project-tracker/bin/registered.py
    side: project
    timeout: 5
```

- Exit code is the verdict: `0` GREEN, `1` YELLOW, `2` RED, `3` NA. First stdout line is the
  headline; the rest is detail.
- A missing command, a timeout, or any other exit code is **YELLOW naming the check** — never a
  crash, and never silence. A hook must not break the session it serves.
- This is what keeps `tracker_registered` alive without putting `projects.yaml` into the
  published engine, which `d-project-tracker-stays-separate` forbids. It is also the only
  extension point a stranger gets.

## Stage 4 — One verdict, and the dedup question

- `rite_session_start.py` emits **one** block covering both halves: the machine/agent checks and
  the project standard. Two hooks writing two lines is what Costin has today and it is the thing
  being removed.
- **Port `hookdedup.py`** into `scripts/`, and cover Rite's own `SessionStart` with it. Its
  window stays configurable (`thresholds.hook_dedup_window_s`), and it stays **fail-open**: a
  duplicated line is far cheaper than a silently missing verdict.

## Stage 5 — preflight shrinks to a config

- Costin's `~/projects/claude-preflight/` keeps `checks.yaml` and nothing executable that Rite
  now provides.
- **Both run side by side until the port is proven**, exactly as the memory mirror does. His
  `settings.json` `SessionStart` entry stays; retiring it is a separate, reversible step and
  **not part of this work**.
- Add a parity gate on the same terms as `test-mirror-port-parity.py`: compare the two engines'
  verdicts on this machine, skip where the original is absent, and **delete the gate when the
  original is retired**.

---

## Verification

- **Stage 1-2:** run the ported engine and the original on this machine and diff the report.
  Same checks, same sides, same verdicts. Any difference is a finding to read, not to smooth over.
- **Stage 3:** a `command:` check that exits 2 must produce RED naming it; one whose command does
  not exist must produce YELLOW, not a traceback. Prove both.
- **Stage 4, the dedup question — measure, do not assume.** Instrument Rite's `SessionStart` to
  append a line per invocation, restart, and count. If it fires once on 2.1.266, `hookdedup` is
  carried for correctness on other entrypoints and **the claim in the docs must say so**, not
  imply a bug that was never observed.
- **Every stage:** `python3 .github/run-gates.py` green, and each new gate proved to FAIL before
  being trusted — break it, watch it fail, restore from a file copy, never `git checkout`.
- **The AST gate is the safety net for the port itself**: `test-portability-rules.py` will fail
  on any `subprocess.run` that arrives without `encoding`/`errors`, and preflight has many.

## Not doing

- **Not retiring Costin's `settings.json` preflight hook.** Side by side first, as with the
  mirror. He has said he will retire the old scripts after testing Rite.
- **Not deleting `preflight.py`.** It stays as the fallback and as the parity oracle.
- **Not porting `mirror_drift` or `last_log_age`** — superseded, by decision.
- **Not shipping `tracker_registered`** in the engine; it becomes a `command:` check in his config.
- **Not touching `projects.yaml`, `next-steps.yaml` or `EVOLUTION.yaml`** — project-tracker's,
  and integration must never be arrived at incrementally.
- Not building any of the eight watchers.
- Not fixing `c-coverage-counts-optional-as-unimplemented` or
  `deleted_ids_appear_in_milestones` — unrelated, and small enough to do any time.
