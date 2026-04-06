#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Bootstrap a workstation from the will repo (Windows). Run as Administrator.
    Phase 1: install git + gh, authenticate
    Phase 2: clone will-personal, read config
    Phase 3: install everything else
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$WillDir = Split-Path -Parent $PSScriptRoot

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "    --: $msg" -ForegroundColor Gray }

# ===========================================================================
# PHASE 1 — git + gh + authenticate
# ===========================================================================

Write-Step "[Phase 1] Checking winget"
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget not found. Install App Installer from the Microsoft Store, then re-run."
    exit 1
}

Write-Step "[Phase 1] git"
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Skip "git"
} else {
    winget install --id Git.Git --silent --accept-package-agreements --accept-source-agreements
    Write-OK "git installed"
}

Write-Step "[Phase 1] GitHub CLI"
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Skip "gh"
} else {
    winget install --id GitHub.cli --silent --accept-package-agreements --accept-source-agreements
    Write-OK "gh installed"
}

Write-Step "[Phase 1] GitHub authentication"
$auth = gh auth status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Skip "already authenticated"
} else {
    gh auth login
}

$GithubUser = (gh api user -q .login).Trim()
Write-OK "Authenticated as: $GithubUser"

# ===========================================================================
# PHASE 2 — Clone will-personal, read config
# ===========================================================================

Write-Step "[Phase 2] Locating will-personal"

$PersonalRepo = "$GithubUser/will-personal"
$DefaultWorkspace = "C:\code"

$repoExists = $false
try {
    gh repo view $PersonalRepo | Out-Null
    $repoExists = $true
} catch {}

if ($repoExists) {
    Write-OK "Found $PersonalRepo"
    $PersonalDir = Join-Path $DefaultWorkspace "will-personal"
    if (-not (Test-Path (Join-Path $PersonalDir ".git"))) {
        New-Item -ItemType Directory -Force -Path $DefaultWorkspace | Out-Null
        gh repo clone $PersonalRepo $PersonalDir
        Write-OK "Cloned will-personal"
    } else {
        Write-Skip "will-personal already cloned"
    }
    $ConfigPath = Join-Path $PersonalDir "config.json"
} else {
    Write-Host "    $PersonalRepo not found on GitHub."
    Write-Host "    Creating config from template..."
    $templateConfig = Join-Path $WillDir "config.example.json"
    $localConfig = Join-Path $WillDir "config.json"
    Copy-Item $templateConfig $localConfig
    Write-Host
    Write-Host "    *** ACTION REQUIRED ***" -ForegroundColor Yellow
    Write-Host "    Edit $localConfig with your details, then re-run."
    exit 0
}

if (-not (Test-Path $ConfigPath)) {
    Write-Error "config.json not found in will-personal."
    exit 1
}

$Cfg       = Get-Content $ConfigPath | ConvertFrom-Json
$GitName   = $Cfg.git.name
$GitEmail  = $Cfg.git.email
$Workspace = $Cfg.workspace.windows
$Repos     = $Cfg.repos

Write-OK "Config loaded: $GitName | workspace: $Workspace"

# ===========================================================================
# PHASE 3 — Full install
# ===========================================================================

Write-Step "[Phase 3] Node.js"
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Skip "node $(node --version)"
} else {
    winget install --id OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
    Write-OK "node installed"
}

Write-Step "[Phase 3] uv"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Skip "uv"
} else {
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    Write-OK "uv installed"
}

Write-Step "[Phase 3] Claude Code"
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Skip "claude"
} else {
    npm install -g @anthropic-ai/claude-code
    Write-OK "Claude Code installed"
}

Write-Step "[Phase 3] ADB (Android platform-tools)"
if (Get-Command adb -ErrorAction SilentlyContinue) {
    Write-Skip "adb"
} else {
    Write-Host "    Download from: https://developer.android.com/studio/releases/platform-tools"
    Write-Host "    Extract to $Workspace\platform-tools and add to PATH"
}

Write-Step "[Phase 3] Git configuration"
git config --global user.name $GitName
git config --global user.email $GitEmail
git config --global init.defaultBranch main
git config --global core.autocrlf true
Write-OK "Git configured"

Write-Step "[Phase 3] Cloning repos to $Workspace"
if (-not (Test-Path $Workspace)) { New-Item -ItemType Directory -Path $Workspace | Out-Null }
foreach ($repo in $Repos) {
    $dest = Join-Path $Workspace $repo
    if (Test-Path (Join-Path $dest ".git")) {
        Write-Skip $repo
    } else {
        gh repo clone "$GithubUser/$repo" $dest
        Write-OK "Cloned $repo"
    }
}

Write-Step "[Phase 3] uv sync"
foreach ($repo in $Repos) {
    $pyproject = Join-Path $Workspace $repo "pyproject.toml"
    if (Test-Path $pyproject) {
        Push-Location (Join-Path $Workspace $repo)
        uv sync
        Pop-Location
        Write-OK "$repo synced"
    } else {
        Write-Skip "$repo (no pyproject.toml)"
    }
}

Write-Step "[Phase 3] Installing Claude Code plugins"
& "$WillDir\plugins\install.ps1"

Write-Host "`n$('=' * 60)" -ForegroundColor Cyan
Write-Host "Bootstrap complete."
Write-Host ""
Write-Host "Manual steps:"
Write-Host "  [ ] Install KDE Connect on this machine and your phone"
Write-Host "  [ ] Enable USB debugging on phone"
Write-Host "  [ ] Install LaTeX: uv run python tools/setup.py  (in health/)"
Write-Host ""
Write-Host "See will/bootstrap/README.md for full notes."
