import pathlib, sys

# retire the concern
p = pathlib.Path("docs/CONCERNS.yaml")
t = p.read_text(encoding="utf-8")
start = t.index("  - id: c-rite-ps1-unreachable-in-production")
end = t.index("  - id: c-readme-sample-output-is-a-copy")
t = t[:start] + t[end:]
retired = '''retired_ids:
  - id: c-rite-ps1-unreachable-in-production
    retired: "2026-09-10"
    how: settled
    outcome: d-git-bash-required-on-windows
    why: >
      Opened and settled the same day. The concern asked whether hooks.json can express a
      per-platform command; the hooks reference answers outright that it cannot, and no single
      command string serves every platform — `bash X` fails under PowerShell, a bare .sh path
      fails under PowerShell, a bare .ps1 path fails under sh, and exec form needs one
      executable name that resolves everywhere, which is the problem the shim exists for.
      SETTLED BY NARROWING THE CLAIM RATHER THAN WIDENING THE CODE. Git Bash is required on
      Windows, hooks.json says `shell: bash` outright, and the spec's coverage row that promised
      a PowerShell path now says hooks do not run there. rite.ps1 stays as a manual entry point.
      The idea NOT taken, recorded so it is not re-proposed as new: two entries with explicit
      `shell:` fields. The docs do not say what a hook declaring an unavailable shell does, and
      building on undocumented behaviour is guessing. Revisit only if that is specified.

'''
t = t.replace("retired_ids:\n", retired, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("concern retired")

# the decision
d = pathlib.Path("docs/DECISIONS.yaml")
dt = d.read_text(encoding="utf-8")
entry = '''
  - id: d-git-bash-required-on-windows
    date: "2026-09-10"
    title: "Git Bash is required on Windows; the PowerShell hook path is withdrawn, not built"
    context: >
      The spec's coverage list promised four rows, the fourth being "Windows without Git for
      Windows -> PowerShell -> the .ps1 shim". hooks.json named `bash rite.sh` for every event
      and never referenced the .ps1, so that row described an intent nothing implemented. CI
      passed the .ps1 throughout by invoking it directly.
    decision: >
      Git Bash is REQUIRED on Windows. Every hooks.json entry declares `shell: bash`. The fourth
      coverage row now says hooks do not run without Git Bash. hooks/rite.ps1 is kept as a
      manual entry point and is not a hook target.
    rationale:
      - >
        A HOOK ENTRY SUPPORTS NO PER-PLATFORM CONDITIONAL — the hooks reference says so
        outright. One command string must serve every platform, and none does: `bash X` fails
        under PowerShell, a bare .sh path fails under PowerShell, a bare .ps1 path fails under
        sh. Exec form skips the shell entirely and would solve it, except it needs one
        executable name resolving everywhere — the exact problem the shim exists for, and this
        development machine has no bare `python` on PATH at all.
      - >
        DECLARING `shell: bash` MAKES THE REQUIREMENT VISIBLE. It changes nothing where Git Bash
        exists; where it does not, it removes a silent fallback to a PowerShell that could only
        fail at our command string. A stated requirement beats an implied one.
      - >
        NARROWING A FALSE CLAIM IS A FIX. The row cost nothing to write and would have cost a
        Windows user their whole install, silently. Withdrawing it is not a retreat from
        portability — CI still runs all three platforms — it is the difference between what
        Rite does and what it once hoped to.
    not_taken: >
      Two hook entries with explicit `shell:` fields, one per platform. The docs do not specify
      what a hook declaring an unavailable shell does — skip, error, or fall back — and building
      on undocumented behaviour is guessing, which is the rule riteyaml and the plan attributor
      both already live by. Revisit if it is ever specified.
    evidence: >
      Answered without a Windows machine, from the vendor docs, after the shipped binary proved
      inconclusive — the authority order that memory rule already prescribes. The binary's
      "hooks.*win32" hits were minified JS spanning long lines, not hook-platform code.
    chosen_by_user: true
    proposed_by: claude
'''
d.write_text(dt.rstrip("\n") + "\n" + entry, encoding="utf-8", newline="\n")
print("decision appended")
