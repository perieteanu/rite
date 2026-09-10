#!/usr/bin/env python3
"""run-gates — run every gate declared in .github/gates.yaml and report honest coverage.

WHY THIS EXISTS RATHER THAN A CHAIN OF `run:` STEPS. Two of Rite's seven gates exit 2 to mean
SKIP: test-riteyaml.py when PyYAML (its oracle, not a dependency) is absent, and
test-installed-current.py when the plugin is not installed — which is always true on a CI
runner. A shell chain has only two answers, so it must either treat those skips as failures or
swallow them into green. Swallowing is the dangerous one: it produces a green badge covering
five sevenths of what it appears to cover.

So this runner distinguishes 0 / 1 / 2 and prints what actually ran. It is the same rule
rite-check.py already applies to itself one level down — a declared rule it cannot implement
reports NA, never silence — applied to the gates instead of to the checks.

It lives in .github/ rather than scripts/ on purpose: scripts/ is one of the four paths
test-installed-current.py compares between the repo and the install cache, so a file added
there would demand a plugin version bump to keep gate 6 green. This is CI plumbing, not part
of the plugin.

Run:  python .github/run-gates.py
Exit: 0 all declared gates passed or skipped as declared · 1 any gate failed
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import riteyaml  # noqa: E402

GATES = ROOT / ".github" / "gates.yaml"

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


def load_gates() -> tuple[list[dict], str]:
    try:
        spec = riteyaml.load(GATES.read_text(encoding="utf-8"), str(GATES))
    except riteyaml.RiteYamlError as exc:
        print(f"FAIL  cannot read the gate list: {exc}", file=sys.stderr)
        raise SystemExit(1)
    return spec["gates"], str(spec.get("python_floor", "unknown"))


def run(gate: dict) -> tuple[str, str, str]:
    """Return (verdict, one-line reason, captured output)."""
    command = gate["command"]
    target = ROOT / command[0]
    if not target.is_file():
        return FAIL, f"no such gate script: {command[0]}", ""

    proc = subprocess.run(
        [sys.executable, str(target), *command[1:]],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    output = (proc.stdout or "") + (proc.stderr or "")

    if proc.returncode == 0:
        return PASS, gate["what"], output
    if proc.returncode == 1:
        return FAIL, gate["what"], output
    if proc.returncode == 2:
        # A skip is only acceptable where the gate list says this gate may skip. An
        # undeclared skip is a surprise, and a surprise that reads as success is the exact
        # shape of failure this runner exists to prevent.
        reason = gate.get("skip_means")
        if not reason:
            return FAIL, (
                f"exited 2 (skip) but declares no `skip_means` in .github/gates.yaml — "
                f"an undeclared skip is not a pass"
            ), output
        return SKIP, " ".join(reason.split()), output
    return FAIL, f"unexpected exit code {proc.returncode} — the contract is 0 pass, 1 fail, 2 skip", output


def main() -> int:
    gates, floor = load_gates()
    width = max(len(g["id"]) for g in gates)

    print(f"rite — gates ({len(gates)} declared, python {sys.version.split()[0]}, "
          f"declared floor {floor})")
    print()

    results = []
    for gate in gates:
        verdict, reason, output = run(gate)
        results.append((gate["id"], verdict, reason))
        print(f"  {verdict:5} {gate['id']:{width}}  {reason}")
        if verdict == FAIL and output.strip():
            for line in output.rstrip().splitlines():
                print(f"        | {line}")
            print()

    ran = [r for r in results if r[1] == PASS]
    failed = [r for r in results if r[1] == FAIL]
    skipped = [r for r in results if r[1] == SKIP]

    print()
    print(f"  {len(gates)} gates · {len(ran)} passed · {len(skipped)} skipped · "
          f"{len(failed)} failed")
    if skipped:
        print(f"  NOT ENFORCED HERE: {', '.join(i for i, _, _ in skipped)}. "
              f"A skip is not a pass.")

    summary(gates, results, floor)
    return 1 if failed else 0


def summary(gates: list[dict], results: list[tuple[str, str, str]], floor: str) -> None:
    """Write the same verdict to the GitHub job summary, where a reader will actually see it."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    ran = sum(1 for _, v, _ in results if v == PASS)
    skipped = [i for i, v, _ in results if v == SKIP]
    lines = [
        "## rite — gates",
        "",
        f"**{ran} of {len(gates)} gates ran.** Python floor {floor}.",
        "",
        "| gate | verdict | detail |",
        "| --- | --- | --- |",
    ]
    for gate_id, verdict, reason in results:
        lines.append(f"| `{gate_id}` | {verdict} | {reason} |")
    if skipped:
        lines += [
            "",
            f"> Not enforced in CI: {', '.join('`' + s + '`' for s in skipped)}. "
            f"A skip is not a pass — these are enforced on a developer machine.",
        ]
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
