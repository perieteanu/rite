# rite.ps1 — launcher shim for Windows without Git Bash, where hooks run under PowerShell.
# A direct translation of rite.sh. One job: find an interpreter, or explain why it cannot.
# No checks, no parsing, no logic. See portability.shell_only_as_a_launcher.
param([Parameter(Position = 0)][string]$Action)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $here ("../scripts/rite_" + ($Action -replace '-', '_') + ".py")

if (-not $Action -or -not (Test-Path $script)) {
    [Console]::Error.WriteLine("rite: no such action '$Action'")
    exit 2
}

# `py` first on Windows: probing bare `python` can trigger the App Execution Alias and open
# the Microsoft Store, which would make the DETECTION cause the surprise it exists to prevent.
foreach ($candidate in @('py', 'python3', 'python')) {
    $found = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($found) { & $found.Source $script; exit $LASTEXITCODE }
}

[Console]::Error.WriteLine(@"
rite: no Python 3 interpreter found (tried py, python3, python).

  Unavailable: the session-start verdict, the checker, the memory mirror, plan copying.
  Still working: /rite:end, /rite:log, /rite:handoff - they need no interpreter.

  Rite will not install anything or change your PATH.
"@)
exit 1
