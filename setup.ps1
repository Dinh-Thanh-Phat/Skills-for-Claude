# Skills-for-Claude — Windows entry point. All logic lives in install.py.
# Usage: .\setup.ps1 [--with-qa-gates] [--with-beads] [--dry-run] ...   (python install.py --help)
$ErrorActionPreference = "Stop"
$py = $null
foreach ($cand in @(@("py", "-3"), @("python"), @("python3"))) {
    try {
        # The Microsoft Store "python" alias exits non-zero instead of running — skip it
        & $cand[0] $cand[1..9] -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $cand; break }
    } catch {}
}
if (-not $py) {
    Write-Host "Python 3.8+ not found. Install it:  winget install Python.Python.3.12  then re-run." -ForegroundColor Yellow
    exit 1
}
& $py[0] $py[1..9] "$PSScriptRoot\install.py" @args
exit $LASTEXITCODE
