import pathlib, sys
p = pathlib.Path("scripts/rite_preflight.py")
t = p.read_text(encoding="utf-8")

def sub(old, new, label):
    global t
    if t.count(old) != 1:
        sys.exit(f"ABORT {label}: matched {t.count(old)}")
    t = t.replace(old, new, 1)
    print(f"  ok  {label}")

# 1 — emit_hook, read_payload, resolve_cwd all go
start = t.index("def emit_hook(results, verdict):")
end = t.index("def main():")
cut = t[start:end]
if "additionalContext" not in cut or "def resolve_cwd" not in cut:
    sys.exit("ABORT: wrong span")
t = t[:start] + '''# THE --hook PATH WAS DELETED ON 2026-09-10, hours after the port brought it over. Nothing
# invoked it: SessionStart runs rite_session_start.py, which calls local_verdict() above and
# folds the result into ONE emission alongside the project standard. emit_hook, read_payload,
# resolve_cwd and a second copy of the dedup all sat here unreachable.
#
# Deleted rather than kept "in case": code that has never run in this codebase is untested code
# presenting as supported, and a second dedup implementation beside ritededup is exactly the
# drift this project attacks. The original still has it, and the original is still the fallback.


''' + t[end:]

# 2 — main loses the hook branches
sub('''    cfg = load_config()
    payload = read_payload(args.hook)
    cwd = resolve_cwd(args.hook, payload)

    # Duplicate dispatch of the same SessionStart: stay silent (emit nothing) and
    # skip the checks entirely — the first firing already wrote last-post.txt.
    # Wrapped: a bug in the dedup path must never cost us the verdict, so any
    # failure here falls through and emits (fail-open, same as the helper).
    if args.hook:
        try:
            if already_emitted(payload, cwd,
                               cfg["thresholds"].get("hook_dedup_window_s", 20),
                               STAMP_PATH):
                sys.exit(0)
        except SystemExit:
            raise
        except Exception:
            pass

    ctx = Ctx(cwd, cfg)
    include_network = args.full and not args.hook  # network never runs in the auto hook
    results = run_checks(ctx, include_network)
    verdict = verdict_of(results)

    write_report(ctx, results, verdict, include_network)
    if args.hook:
        emit_hook(results, verdict)
    else:
        print_human(ctx, results, verdict, include_network)
    sys.exit(0)  # never block the session''',
    '''    cfg = load_config()
    ctx = Ctx(Path.cwd().resolve(), cfg)
    results = run_checks(ctx, args.full)
    verdict = verdict_of(results)

    write_report(ctx, results, verdict, args.full)
    print_human(ctx, results, verdict, args.full)
    return 0''',
    "main body")

# 3 — the flag and its docstring line
sub('''    ap.add_argument("--hook", action="store_true",
                    help="hook mode: emit verdict JSON for additionalContext")
''', "", "flag")
sub('''  preflight.py --hook    Called by the SessionStart hook. Runs the LOCAL tier, writes
                         the full report to last-post.txt, and emits ONLY a verdict to
                         context via hookSpecificOutput.additionalContext (JSON, exit 0):
                           GREEN  -> one terse line
                           YELLOW/RED -> verdict + only the failing checks + report path
                         Always exits 0 (never blocks session start).
                         Deduplicated: the VS Code extension dispatches one
                         SessionStart twice (~47ms apart), so a repeat of the
                         same session_id+source is suppressed (see already_emitted;
                         window: checks.yaml thresholds.hook_dedup_window_s).
''', '''  (no --hook mode)       SessionStart goes through rite_session_start.py, which calls
                         local_verdict() and folds the POST into one emission with the project
                         standard. Dedup lives there too, in ritededup.
''', "docstring")

# 4 — already_emitted is no longer used here
sub("already_emitted = ritededup.already_emitted\n\n\n", "", "dedup alias")
sub("import ritededup  # noqa: E402\n", "", "dedup import")

p.write_text(t, encoding="utf-8", newline="\n")
print(f"rite_preflight.py: {len(p.read_bytes())} bytes")
