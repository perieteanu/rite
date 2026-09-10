import pathlib, sys
p = pathlib.Path("scripts/rite-check.py")
t = p.read_text(encoding="utf-8")

old = '''        for test in art.get("tests") or []:
            declared += 1
            rule_name = test.get("rule")
            # Coverage is about what this checker CAN do, not about which files this
            # project happens to carry — otherwise an absent optional artifact would
            # read as missing checker capability.
            if rule_name in RULES:
                implemented += 1'''
new = '''        for test in art.get("tests") or []:
            rule_name = test.get("rule")
            # Coverage is about what this checker CAN do, not about which files this
            # project happens to carry — otherwise an absent optional artifact would
            # read as missing checker capability.
            #
            # `optional` IS NOT A RULE AWAITING IMPLEMENTATION. It is a marker meaning the
            # artifact is not required, handled by its own branch and deliberately absent from
            # RULES. Counting it in the denominator understated the checker by four instances
            # and, worse, four documents repeated "seven declared tests unimplemented" for days
            # on the strength of that line, read as a to-do list it never was.
            # c-coverage-counts-optional-as-unimplemented.
            if rule_name in MARKER_RULES:
                continue
            declared += 1
            if rule_name in RULES:
                implemented += 1'''
if t.count(old) != 1:
    sys.exit("ABORT counter")
t = t.replace(old, new, 1)

# the same exclusion in the unparseable branch, so a broken file cannot skew coverage either
old2 = '''            for test in art.get("tests") or []:
                declared += 1
                if test.get("rule") in RULES:
                    implemented += 1'''
new2 = '''            for test in art.get("tests") or []:
                if test.get("rule") in MARKER_RULES:
                    continue
                declared += 1
                if test.get("rule") in RULES:
                    implemented += 1'''
if t.count(old2) != 1:
    sys.exit("ABORT unparseable counter")
t = t.replace(old2, new2, 1)

# declare the marker set beside RULES
old3 = "RULES = {}\n"
new3 = '''RULES = {}

# Rules that are MARKERS rather than checks: they declare something about the artifact and are
# handled by an explicit branch, never by a RULES entry. They are excluded from the coverage
# denominator, because "unimplemented" should mean work outstanding.
MARKER_RULES = frozenset({"optional"})
'''
if t.count(old3) != 1:
    sys.exit("ABORT rules decl")
t = t.replace(old3, new3, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("coverage denominator fixed")
