"""Differential measurement: riteyaml vs PyYAML over every YAML file in the portfolio.

Question: if Rite checks that ALL project YAML parses, how often is riteyaml's verdict wrong?
  AGREE          both parse, identical structure
  MISREAD        both parse, structures differ           (irrelevant to validity, matters for reading)
  TRUE_INVALID   PyYAML rejects, riteyaml rejects        (the check works)
  FALSE_ACCEPT   PyYAML rejects, riteyaml accepts        (false GREEN)
  REFUSED        PyYAML accepts, riteyaml rejects        (false RED unless the subset is declared)
  CRASH          riteyaml raised something that is not RiteYamlError (a bug)
"""
from __future__ import annotations

import collections
import importlib.util
import re
import sys
from pathlib import Path

R = Path("/home/perieteanu/projects/rite/scripts")
sys.path.insert(0, str(R))
import riteyaml  # noqa: E402
import yaml  # noqa: E402

spec = importlib.util.spec_from_file_location("t", R / "test-riteyaml.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)

corpus = Path(sys.argv[1]).read_text(encoding="utf-8").split("\n")
buckets = collections.defaultdict(list)
reasons = collections.Counter()
reasons_docs = collections.Counter()
diffkinds = collections.Counter()
multidoc = 0

for path in filter(None, corpus):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    in_docs = bool(re.search(r"/docs[^/]*/", path))
    try:
        py, py_ok = yaml.safe_load(text), True
    except yaml.composer.ComposerError:
        try:
            py, py_ok = list(yaml.safe_load_all(text)), True
            multidoc += 1
        except yaml.YAMLError:
            py_ok = False
    except yaml.YAMLError:
        py_ok = False
    try:
        ry, ry_ok, why = riteyaml.load(text, "f"), True, ""
    except riteyaml.RiteYamlError as e:
        ry_ok, why = False, str(e).splitlines()[0].split(": ", 1)[-1]
    except Exception as e:  # noqa: BLE001
        buckets["CRASH"].append((path, f"{type(e).__name__}: {e}"[:120], in_docs))
        continue
    if py_ok and ry_ok:
        diffs = list(t.differences(py, ry))
        if diffs:
            kind = re.sub(r"^\$[^:]*: ", "", diffs[0])
            kind = re.sub(r"'[^']*'|\"[^\"]*\"|\d+", "_", kind)[:70]
            diffkinds[kind] += 1
            buckets["MISREAD"].append((path, diffs[0][:120], in_docs))
        else:
            buckets["AGREE"].append((path, "", in_docs))
    elif not py_ok and not ry_ok:
        buckets["TRUE_INVALID"].append((path, why, in_docs))
    elif not py_ok:
        buckets["FALSE_ACCEPT"].append((path, "", in_docs))
    else:
        buckets["REFUSED"].append((path, why, in_docs))
        reasons[why] += 1
        if in_docs:
            reasons_docs[why] += 1

total = sum(len(v) for v in buckets.values())
print(f"files: {total}   (PyYAML needed safe_load_all for {multidoc} multi-document files)\n")
print(f"{'bucket':14} {'all':>5} {'docs*/':>7}")
for b in ["AGREE", "MISREAD", "TRUE_INVALID", "FALSE_ACCEPT", "REFUSED", "CRASH"]:
    v = buckets[b]
    print(f"{b:14} {len(v):5} {sum(1 for x in v if x[2]):7}")

print("\nREFUSED — reason (all / docs*/):")
for why, n in reasons.most_common():
    print(f"  {n:4} {reasons_docs[why]:4}  {why}")

print("\nMISREAD — first difference, normalised:")
for k, n in diffkinds.most_common(12):
    print(f"  {n:4}  {k}")

for b in ["FALSE_ACCEPT", "CRASH", "TRUE_INVALID"]:
    if buckets[b]:
        print(f"\n{b}:")
        for p, d, _ in buckets[b][:25]:
            print(f"  {p}  {d}")

print("\nREFUSED under docs*/ by project:")
by = collections.Counter(p.split("/")[4] for p, _, d in buckets["REFUSED"] if d)
print("  " + ", ".join(f"{k} {v}" for k, v in by.most_common()))
print("\nMISREAD under docs*/ by project:")
by = collections.Counter(p.split("/")[4] for p, _, d in buckets["MISREAD"] if d)
print("  " + ", ".join(f"{k} {v}" for k, v in by.most_common()))
