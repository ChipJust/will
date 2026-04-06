#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Bootstrap Chip's development workstation on Windows.
    Run as Administrator from the will repo root.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$WORKSPACE = "D:\_code"
$GIT_USER_NAME = "Chip Ueltschey"
$GIT_USER_EMAIL = "chip@chipjust.com"   # update if email changes
$GITHUB_USER = "ChipJust"

$REPOS = @(
    "will",
    "health",
    "writing",
    "vibedaw",
    "money"
    # Add: "giving", "prayer", "social-influence" when created
)

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "    --: $msg" -ForegroundColor Gray }

# ---------------------------------------------------------------------------
# 1. Winget
# ---------------------------------------------------------------------------
Write-Step "Checking winget"
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "winget not found. Install App Installer from the Microsoft Store, then re-run." -ForegroundColor Red
    exit 1
}
Write-OK "winget available"

# ---------------------------------------------------------------------------
# 2. Core tools
# ---------------------------------------------------------------------------
$tools = @{
    "Git.Git"               = "git"
    "GitHub.cli"            = "gh"
    "OpenJS.NodeJS.LTS"     = "node"
    "Google.AndroidStudio"  = $null   # provides adb; or install platform-tools directly
}

Write-Step "Installing core tools via winget"
foreach ($pkg in $tools.Keys) {
    $cmd = $tools[$pkg]
    if ($cmd -and (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Skip "$pkg already installed"
    } else {
        Write-Host "    Installing $pkg..."
        winget install --id $pkg --silent --accept-package-agreements --accept-source-agreements
    }
}

# uv — installed via its own installer, not winget
Write-Step "Installing uv"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Skip "uv already installed"
} else {
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    Write-OK "uv installed"
}

# Android platform-tools (adb) — standalone, no full Android Studio needed
Write-Step "Checking ADB (Android platform-tools)"
if (Get-Command adb -ErrorAction SilentlyContinue) {
    Write-Skip "adb already available"
} else {
    Write-Host "    Download Android platform-tools from:"
    Write-Host "    https://developer.android.com/studio/releases/platform-tools"
    Write-Host "    Extract to $WORKSPACE\platform-tools and add to PATH"
}

# ---------------------------------------------------------------------------
# 3. Claude Code
# ---------------------------------------------------------------------------
Write-Step "Installing Claude Code"
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Skip "claude already installed"
} else {
    npm install -g @anthropic-ai/claude-code
    Write-OK "Claude Code installed"
}

# ---------------------------------------------------------------------------
# 4. Git configuration
# ---------------------------------------------------------------------------
Write-Step "Configuring Git"
git config --global user.name $GIT_USER_NAME
git config --global user.email $GIT_USER_EMAIL
git config --global init.defaultBranch main
git config --global core.autocrlf true
Write-OK "Git configured for $GIT_USER_NAME"

# ---------------------------------------------------------------------------
# 5. GitHub authentication
# ---------------------------------------------------------------------------
Write-Step "GitHub CLI authentication"
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Skip "Already authenticated with GitHub"
} else {
    Write-Host "    Launching interactive GitHub login..."
    gh auth login
}

# ---------------------------------------------------------------------------
# 6. Clone repos
# ---------------------------------------------------------------------------
Write-Step "Cloning repos to $WORKSPACE"
if (-not (Test-Path $WORKSPACE)) { New-Item -ItemType Directory -Path $WORKSPACE | Out-Null }

foreach ($repo in $REPOS) {
    $dest = Join-Path $WORKSPACE $repo
    if (Test-Path $dest) {
        Write-Skip "$repo already cloned"
    } else {
        Write-Host "    Cloning $GITHUB_USER/$repo..."
        gh repo clone "$GITHUB_USER/$repo" $dest
        Write-OK "Cloned $repo"
    }
}

# ---------------------------------------------------------------------------
# 7. uv sync in each repo
# ---------------------------------------------------------------------------
Write-Step "Running uv sync in repos with pyproject.toml"
foreach ($repo in $REPOS) {
    $pyproject = Join-Path $WORKSPACE $repo "pyproject.toml"
    if (Test-Path $pyproject) {
        Write-Host "    uv sync: $repo..."
        Push-Location (Join-Path $WORKSPACE $repo)
        uv sync
        Pop-Location
        Write-OK "$repo synced"
    } else {
        Write-Skip "$repo has no pyproject.toml"
    }
}

# ---------------------------------------------------------------------------
# 8. Post-setup checklist
# ---------------------------------------------------------------------------
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "Bootstrap complete. Manual steps remaining:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  [ ] Install KDE Connect on this machine and on Pixel 7"
Write-Host "  [ ] Install Syncthing if folder sync needed"
Write-Host "  [ ] Verify ingest tooling: uv run python tools/ingest.py --help (in health/)"
Write-Host "  [ ] Install LaTeX if PDF generation needed (uv run python tools/setup.py in health/)"
Write-Host "  [ ] Add AI model weights to D:\_code\models\ when ready"
Write-Host "  [ ] Update GIT_USER_EMAIL in this script if email has changed"
Write-Host ""
Write-Host "See will/bootstrap/README.md for full post-setup checklist." -ForegroundColor Gray
