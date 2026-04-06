#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Bootstrap a workstation from the will repo (Windows).
    Run as Administrator from the will repo root.

    Requires config.json in the repo root (copy from config.example.json).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$WillDir = Split-Path -Parent $PSScriptRoot
$Config = Join-Path $WillDir "config.json"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "    --: $msg" -ForegroundColor Gray }

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
Write-Step "Reading config.json"
if (-not (Test-Path $Config)) {
    Write-Error "config.json not found. Copy config.example.json to config.json and fill it in."
    exit 1
}
$Cfg = Get-Content $Config | ConvertFrom-Json
$GitName    = $Cfg.git.name
$GitEmail   = $Cfg.git.email
$GithubUser = $Cfg.github.username
$Workspace  = $Cfg.workspace.windows
$Repos      = $Cfg.repos

Write-OK "Name: $GitName | GitHub: $GithubUser | Workspace: $Workspace"

# ---------------------------------------------------------------------------
# Winget check
# ---------------------------------------------------------------------------
Write-Step "Checking winget"
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget not found. Install App Installer from the Microsoft Store, then re-run."
    exit 1
}
Write-OK "winget available"

# ---------------------------------------------------------------------------
# Core tools via winget
# ---------------------------------------------------------------------------
$WingetPkgs = @{
    "Git.Git"      = "git"
    "GitHub.cli"   = "gh"
    "OpenJS.NodeJS.LTS" = "node"
}

Write-Step "Installing tools via winget"
foreach ($pkg in $WingetPkgs.Keys) {
    $cmd = $WingetPkgs[$pkg]
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        Write-Skip "$pkg"
    } else {
        Write-Host "    Installing $pkg..."
        winget install --id $pkg --silent --accept-package-agreements --accept-source-agreements
        Write-OK "$pkg installed"
    }
}

# ---------------------------------------------------------------------------
# uv
# ---------------------------------------------------------------------------
Write-Step "uv"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Skip "uv"
} else {
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    Write-OK "uv installed"
}

# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------
Write-Step "Claude Code"
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Skip "claude"
} else {
    npm install -g @anthropic-ai/claude-code
    Write-OK "Claude Code installed"
}

# ---------------------------------------------------------------------------
# ADB (Android platform-tools)
# ---------------------------------------------------------------------------
Write-Step "ADB (Android platform-tools)"
if (Get-Command adb -ErrorAction SilentlyContinue) {
    Write-Skip "adb"
} else {
    Write-Host "    Download platform-tools from:"
    Write-Host "    https://developer.android.com/studio/releases/platform-tools"
    Write-Host "    Extract to $Workspace\platform-tools and add to PATH"
}

# ---------------------------------------------------------------------------
# Git config
# ---------------------------------------------------------------------------
Write-Step "Git configuration"
git config --global user.name $GitName
git config --global user.email $GitEmail
git config --global init.defaultBranch main
git config --global core.autocrlf true
Write-OK "Git configured"

# ---------------------------------------------------------------------------
# GitHub auth
# ---------------------------------------------------------------------------
Write-Step "GitHub authentication"
$auth = gh auth status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Skip "already authenticated"
} else {
    gh auth login
}

# ---------------------------------------------------------------------------
# Clone repos
# ---------------------------------------------------------------------------
Write-Step "Cloning repos to $Workspace"
if (-not (Test-Path $Workspace)) { New-Item -ItemType Directory -Path $Workspace | Out-Null }

foreach ($repo in $Repos) {
    $dest = Join-Path $Workspace $repo
    if (Test-Path (Join-Path $dest ".git")) {
        Write-Skip $repo
    } else {
        Write-Host "    Cloning $GithubUser/$repo..."
        gh repo clone "$GithubUser/$repo" $dest
        Write-OK "Cloned $repo"
    }
}

# ---------------------------------------------------------------------------
# uv sync
# ---------------------------------------------------------------------------
Write-Step "uv sync in repos with pyproject.toml"
foreach ($repo in $Repos) {
    $pyproject = Join-Path $Workspace $repo "pyproject.toml"
    if (Test-Path $pyproject) {
        Write-Host "    uv sync: $repo"
        Push-Location (Join-Path $Workspace $repo)
        uv sync
        Pop-Location
        Write-OK "$repo synced"
    } else {
        Write-Skip "$repo (no pyproject.toml)"
    }
}

# ---------------------------------------------------------------------------
# Install will plugins into Claude Code
# ---------------------------------------------------------------------------
Write-Step "Installing Claude Code plugins"
& "$WillDir\plugins\install.ps1"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host "`n$('=' * 60)" -ForegroundColor Cyan
Write-Host "Bootstrap complete." -ForegroundColor Cyan
Write-Host ""
Write-Host "Manual steps:"
Write-Host "  [ ] Install KDE Connect on this machine and on your phone"
Write-Host "  [ ] Enable USB debugging on phone (Settings > Developer Options)"
Write-Host "  [ ] Install LaTeX for PDF generation: uv run python tools/setup.py  (in health/)"
Write-Host ""
Write-Host "See will/bootstrap/README.md for full notes."
