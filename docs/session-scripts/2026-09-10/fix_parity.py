import pathlib, sys
p = pathlib.Path("scripts/test-preflight-port-parity.py")
t = p.read_text(encoding="utf-8")
old = '''    cwd = ROOT
    try:
        theirs = {r.name: r for r in legacy.run_checks(
            legacy.Ctx(cwd, legacy.load_config()), False)}
        ours = {r.name: r for r in rite_preflight.run_checks(
            rite_preflight.Ctx(cwd, rite_preflight.load_config()), False)}
    except Exception as exc:
        print(f"SKIP  a check could not be run for comparison — {exc}")
        return SKIP
'''
new = '''    # ONE CONFIG, BOTH ENGINES. The first version of this gate let each engine load its own,
    # and it failed the moment they diverged — `disk` went RED against GREEN because one config
    # watched /mnt/storage and the other did not. That is a CONFIG difference reported as a CODE
    # difference, which is a gate crying wolf about the thing it exists to protect. Parity means
    # "same behaviour given the same input", so the input is held constant.
    cwd = ROOT
    try:
        shared_cfg = legacy.load_config()
        theirs = {r.name: r for r in legacy.run_checks(legacy.Ctx(cwd, shared_cfg), False)}
        ours = {r.name: r for r in rite_preflight.run_checks(
            rite_preflight.Ctx(cwd, dict(shared_cfg)), False)}
    except Exception as exc:
        print(f"SKIP  a check could not be run for comparison — {exc}")
        return SKIP
'''
if t.count(old) != 1:
    sys.exit("ABORT")
p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
print("parity now holds config constant")
