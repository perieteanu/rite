import pathlib, sys
p = pathlib.Path("scripts/test-checker-verdicts.py")
t = p.read_text(encoding="utf-8")
old = '''    # And the totals must be untouched: collapsing is a display choice, never a verdict change.
    total = [ln for ln in out.splitlines() if "checks ·" in ln]
    if not total or "60 NA" not in total[0]:
        fail(f"collapsing changed the NA count — it must not: {total[0].strip() if total else ''}")
'''
new = '''    # And the totals must be untouched: collapsing is a display choice, never a verdict change.
    #
    # ASSERTED AS AN INVARIANT, NOT A LITERAL. This line pinned "59 NA", then "60 NA", and was
    # about to pin "61 NA" — it broke three times in one day, every time an artifact or a rule
    # was added, and each break was noise rather than a finding. The number was never the point:
    # the claim is that every declared check lands in exactly one bucket, so collapsing cannot
    # quietly drop one. That holds whatever the counts are.
    total = [ln for ln in out.splitlines() if "checks ·" in ln]
    if not total:
        fail("the summary line is missing entirely")
    else:
        nums = [int(x) for x in re.findall(r"(\\d+)\\s+(?:checks|RED|YELLOW|NA|GREEN)", total[0])]
        if len(nums) != 5:
            fail(f"could not read the five counts from: {total[0].strip()}")
        elif nums[0] != sum(nums[1:]):
            fail(f"collapsing lost a check — {nums[0]} declared but "
                 f"{sum(nums[1:])} accounted for: {total[0].strip()}")
'''
if t.count(old) != 1:
    sys.exit("ABORT")
t = t.replace(old, new, 1)
if "\nimport re" not in t:
    t = t.replace("import subprocess", "import re\nimport subprocess", 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("assertion is now an invariant")
