import pathlib, sys
p = pathlib.Path("scripts/rite_preflight.py")
t = p.read_text(encoding="utf-8")

# 1 — the writer
anchor = "# ─── context passed to each check ───────────────────────────────────────────"
new = '''TEMPLATE_CONFIG = HERE.parent / "template" / "checks.yaml"


def init_config():
    """Write the documented default config, if there is not one already.

    WHY THIS EXISTS: template/checks.yaml shipped with the port and nothing installed it, so a
    user got the shipped defaults and never learned the file existed — or that `command:` checks
    were available at all. rite_init.py could not do it: that seeds a PROJECT, and this is
    user-level config under ${CLAUDE_PLUGIN_DATA}.

    NEVER OVERWRITES. The same rule the scaffolder follows: an existing file is reported and
    left alone, because a config the user has edited is theirs.
    """
    if ritefs.exists_exactly(CONFIG_PATH):
        print(f"exists, unchanged: {CONFIG_PATH}")
        return 0
    if not ritefs.exists_exactly(TEMPLATE_CONFIG):
        print(f"FAIL  the shipped default is missing: {TEMPLATE_CONFIG}", file=sys.stderr)
        return 1
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(TEMPLATE_CONFIG.read_text(encoding="utf-8"),
                           encoding="utf-8", newline="\\n")
    print(f"wrote {CONFIG_PATH}")
    print("Every value in it is optional — deleting the file restores the shipped defaults.")
    return 0


# ─── context passed to each check ───────────────────────────────────────────'''
if t.count(anchor) != 1:
    sys.exit("ABORT anchor")
t = t.replace(anchor, new, 1)

# 2 — the flag
old_flag = '''    ap.add_argument("--full", action="store_true",'''
new_flag = '''    ap.add_argument("--init-config", action="store_true",
                    help="write the documented default checks.yaml if absent; never overwrites")
    ap.add_argument("--full", action="store_true",'''
if t.count(old_flag) != 1:
    sys.exit("ABORT flag")
t = t.replace(old_flag, new_flag, 1)

# 3 — dispatch, before anything else runs
old_disp = "    args = ap.parse_args()"
if t.count(old_disp) != 1:
    sys.exit("ABORT dispatch")
t = t.replace(old_disp,
              "    args = ap.parse_args()\n\n    if args.init_config:\n        return init_config()", 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("--init-config added")
