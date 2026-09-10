# rite.ps1 — launcher shim for Windows without Git Bash, where hooks run under PowerShell.
# A direct translation of rite.sh. One job: find an interpreter, or explain why it cannot.
# No checks, no parsing, no logic. See portability.shell_only_as_a_launcher.
param(
    [Parameter(Position = 0)][string]$Action,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

# An explicit table, not name-mangling — see the same block in rite.sh. The checker is
# rite-check.py with a hyphen; the session entry points use underscores.
$leaf = switch ($Action) {
    'session-start' { 'rite_session_start.py' }
    'session-end'   { 'rite_session_end.py' }
    'check'         { 'rite-check.py' }
    'copy'          { 'rite_copy.py' }
    default         { $null }
}
$script = if ($leaf) { Join-Path $here ("../scripts/" + $leaf) } else { $null }

if (-not $script -or -not (Test-Path $script)) {
    [Console]::Error.WriteLine("rite: no such action '$Action' (session-start, session-end, check, copy)")
    exit 2
}

# `py` first on Windows: probing bare `python` can trigger the App Execution Alias and open
# the Microsoft Store, which would make the DETECTION cause the surprise it exists to prevent.
foreach ($candidate in @('py', 'python3', 'python')) {
    $found = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($found) { & $found.Source $script @Rest; exit $LASTEXITCODE }
}

[Console]::Error.WriteLine(@"
rite: no Python 3 interpreter found (tried py, python3, python).

  Unavailable: the session-start verdict, the checker, the memory mirror, plan copying.
  Still working: /rite:end, /rite:log, /rite:handoff - they need no interpreter.

  Rite will not install anything or change your PATH.
"@)
exit 1
