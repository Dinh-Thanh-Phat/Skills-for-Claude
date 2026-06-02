# Skills-for-Claude - Windows Setup Script
# Run from repo root: .\setup.ps1
# Requires: Git Bash or PowerShell 5+

param(
    [switch]$Force,
    [switch]$SkipSettings
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$ClaudeDir = "$env:USERPROFILE\.claude"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    [!!] $msg" -ForegroundColor Yellow }

Write-Host "`nSkills-for-Claude Setup" -ForegroundColor White
Write-Host "=======================" -ForegroundColor White

# 1. Skills
Write-Step "Installing skills to $ClaudeDir\skills\"
$skillsSrc = "$RepoRoot\skills"
$skillsDst = "$ClaudeDir\skills"
if (-not (Test-Path $skillsDst)) { New-Item -ItemType Directory -Force $skillsDst | Out-Null }
$skills = Get-ChildItem $skillsSrc -Directory
foreach ($skill in $skills) {
    $dst = "$skillsDst\$($skill.Name)"
    if ((Test-Path $dst) -and -not $Force) {
        Write-Warn "Skipping $($skill.Name) (exists - use -Force to overwrite)"
    } else {
        Copy-Item -Recurse -Force $skill.FullName $skillsDst
        Write-Ok $skill.Name
    }
}
Write-Host "    $($skills.Count) skills processed" -ForegroundColor Gray

# 2. Hooks
Write-Step "Installing hooks to $ClaudeDir\hooks\"
$hooksSrc = "$RepoRoot\hooks"
$hooksDst = "$ClaudeDir\hooks"
if (-not (Test-Path $hooksDst)) { New-Item -ItemType Directory -Force $hooksDst | Out-Null }
Copy-Item -Force "$hooksSrc\fix-flat-skill.py" $hooksDst
Write-Ok "fix-flat-skill.py"

# 3. Shared context
Write-Step "Installing shared-context to $ClaudeDir\shared-context\"
$ctxSrc = "$RepoRoot\shared-context"
$ctxDst = "$ClaudeDir\shared-context"

# memories/_shared.md — merge if exists, else copy
$sharedMem = "$ctxDst\memories\_shared.md"
if (-not (Test-Path "$ctxDst\memories")) { New-Item -ItemType Directory -Force "$ctxDst\memories" | Out-Null }
if ((Test-Path $sharedMem) -and -not $Force) {
    Write-Warn "_shared.md already exists - skipping (use -Force to overwrite)"
} else {
    Copy-Item -Force "$ctxSrc\memories\_shared.md" "$ctxDst\memories\_shared.md"
    Write-Ok "memories/_shared.md"
}

# knowledge/
if (-not (Test-Path "$ctxDst\knowledge")) { New-Item -ItemType Directory -Force "$ctxDst\knowledge" | Out-Null }
Get-ChildItem "$ctxSrc\knowledge" -File | ForEach-Object {
    $dst = "$ctxDst\knowledge\$($_.Name)"
    if ((Test-Path $dst) -and -not $Force) {
        Write-Warn "knowledge/$($_.Name) exists - skipping"
    } else {
        Copy-Item -Force $_.FullName $dst
        Write-Ok "knowledge/$($_.Name)"
    }
}

# 4. Settings (optional)
if (-not $SkipSettings) {
    Write-Step "Settings configuration"
    $settingsFile = "$ClaudeDir\settings.json"
    if (Test-Path $settingsFile) {
        Write-Warn "settings.json exists. Review config\settings.template.json manually."
        Write-Host "    Key things to add to your settings.json:" -ForegroundColor Gray
        Write-Host "    - hooks (PostToolUse, PreCompact, SessionStart)" -ForegroundColor Gray
        Write-Host "    - enabledPlugins" -ForegroundColor Gray
        Write-Host "    - extraKnownMarketplaces" -ForegroundColor Gray
    } else {
        Copy-Item -Force "$RepoRoot\config\settings.template.json" $settingsFile
        Write-Ok "settings.json created from template"
    }
}

# 5. Project example skills
Write-Step "Project-example skills"
Write-Host "    project-example\.claude\skills\ contains:" -ForegroundColor Gray
Get-ChildItem "$RepoRoot\project-example\.claude\skills" -Directory | ForEach-Object {
    Write-Host "      - $($_.Name)" -ForegroundColor Gray
}
Write-Host "    Copy these to your project's .claude\skills\ as needed." -ForegroundColor Gray

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "Restart Claude Code to activate skills and hooks.`n" -ForegroundColor White
