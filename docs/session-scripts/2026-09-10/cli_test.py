import pathlib, sys
p = pathlib.Path("scripts/test-checker-verdicts.py")
t = p.read_text(encoding="utf-8")
old = """if failures:
    print(f"\\n{len(failures)} FAILED")
    sys.exit(1)
print("PASS  unparseable is RED and named; absent stays NA; a broken marker is reported;\\n"
      "      declared claims are checked against the tree and an undeclared one is nudged;\\n"
      "      stage gates what is required, a declaration beats tier, and no stage means no\\n"
      "      leniency.")
"""
new = '''# ── the CLI contract ─────────────────────────────────────────────────────────
# Until 2026-09-10 every unrecognised flag was silently discarded: `--help` ran a full check,
# and a typo'd `--exclude-scpoe=session` scored at FULL strength while the caller believed a
# scope had been excluded. A flag that looks accepted and does nothing is a silent wrong
# answer — the failure class this project attacks, in its own entry point. These cases exist
# so it cannot come back.
def cli(*argv: str) -> tuple[int, str, str]:
    out = subprocess.run([sys.executable, str(CHECKER), *argv],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return out.returncode, out.stdout, out.stderr


code, out, _ = cli("--help")
if code != 0:
    fail(f"--help exited {code}, expected 0")
if "Usage:" not in out or "--exclude-scope=SCOPE" not in out:
    fail("--help printed no usage naming the real flags")
if "checks ·" in out:
    fail("--help RAN A CHECK instead of printing usage — the original defect")

code, _, err = cli("--exclude-scpoe=session")
if code != 2:
    fail(f"a typo'd flag exited {code}, expected 2 — it must not be silently ignored")
if "--exclude-scpoe=session" not in err:
    fail("the unknown flag was rejected without naming it")

code, _, err = cli("--exclude-scope", "session")
if code != 2:
    fail(f"the separate form exited {code}, expected 2 — a bare value reads as PROJECT_DIR")
if "with an '='" not in err:
    fail("the separate form was rejected without suggesting the joined one")

code, out, _ = cli(str(ROOT), "--force", "--exclude-scope=session")
if code not in (0, 1):
    fail(f"a fully valid invocation exited {code}")
if "checks ·" not in out:
    fail("a valid invocation did not run a check")

if failures:
    print(f"\\n{len(failures)} FAILED")
    sys.exit(1)
print("PASS  unparseable is RED and named; absent stays NA; a broken marker is reported;\\n"
      "      declared claims are checked against the tree and an undeclared one is nudged;\\n"
      "      stage gates what is required, a declaration beats tier, and no stage means no\\n"
      "      leniency; unknown flags are rejected rather than swallowed.")
'''
if t.count(old) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("CLI cases added")
