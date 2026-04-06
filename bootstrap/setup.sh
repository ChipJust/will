#!/usr/bin/env bash
# Bootstrap a workstation from the will repo.
# Run from the will repo root: bash bootstrap/setup.sh
#
# Requires config.json in the repo root (copy from config.example.json).

set -euo pipefail

WILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$WILL_DIR/config.json"

step()  { echo; echo "==> $*"; }
ok()    { echo "    OK: $*"; }
skip()  { echo "    --: $* (already done)"; }
die()   { echo "ERROR: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
step "Reading config.json"
[ -f "$CONFIG" ] || die "config.json not found. Copy config.example.json to config.json and fill it in."

GIT_NAME=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(d['git']['name'])")
GIT_EMAIL=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(d['git']['email'])")
GITHUB_USER=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(d['github']['username'])")
WORKSPACE=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(d['workspace']['linux'])")
WORKSPACE="${WORKSPACE/#\~/$HOME}"
REPOS=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(' '.join(d['repos']))")
read -ra REPOS <<< "$REPOS"

ok "Name: $GIT_NAME | GitHub: $GITHUB_USER | Workspace: $WORKSPACE"

# ---------------------------------------------------------------------------
# Detect package manager
# ---------------------------------------------------------------------------
if command -v apt-get &>/dev/null; then
    PKG="sudo apt-get install -y"
    sudo apt-get update -qq
elif command -v dnf &>/dev/null; then
    PKG="sudo dnf install -y"
elif command -v brew &>/dev/null; then
    PKG="brew install"
    brew update
else
    die "No supported package manager found (apt, dnf, brew)."
fi

# ---------------------------------------------------------------------------
# Core packages
# ---------------------------------------------------------------------------
step "Installing system packages"
$PKG git curl wget build-essential 2>/dev/null || $PKG git curl wget

# ---------------------------------------------------------------------------
# GitHub CLI
# ---------------------------------------------------------------------------
step "GitHub CLI"
if command -v gh &>/dev/null; then
    skip "gh $(gh --version | head -1)"
else
    if command -v apt-get &>/dev/null; then
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
            | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
            https://cli.github.com/packages stable main" \
            | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
        sudo apt-get update -qq && sudo apt-get install -y gh
    else
        $PKG gh
    fi
    ok "gh installed"
fi

# ---------------------------------------------------------------------------
# Node.js (via nvm)
# ---------------------------------------------------------------------------
step "Node.js"
if command -v node &>/dev/null; then
    skip "node $(node --version)"
else
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    # shellcheck disable=SC1091
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install --lts
    ok "node $(node --version)"
fi

# ---------------------------------------------------------------------------
# uv
# ---------------------------------------------------------------------------
step "uv"
if command -v uv &>/dev/null; then
    skip "uv $(uv --version)"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    ok "uv installed"
fi

# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------
step "Claude Code"
if command -v claude &>/dev/null; then
    skip "claude already installed"
else
    npm install -g @anthropic-ai/claude-code
    ok "Claude Code installed"
fi

# ---------------------------------------------------------------------------
# Android platform-tools (adb)
# ---------------------------------------------------------------------------
step "ADB (Android platform-tools)"
if command -v adb &>/dev/null; then
    skip "adb"
else
    $PKG android-tools-adb 2>/dev/null || {
        echo "    Downloading platform-tools..."
        curl -O "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
        unzip -q platform-tools-latest-linux.zip -d "$HOME"
        rm platform-tools-latest-linux.zip
        echo "export PATH=\"\$HOME/platform-tools:\$PATH\"" >> "$HOME/.bashrc"
        export PATH="$HOME/platform-tools:$PATH"
    }
    ok "adb ready"
fi

# ---------------------------------------------------------------------------
# KDE Connect
# ---------------------------------------------------------------------------
step "KDE Connect (phone integration)"
if command -v kdeconnect-cli &>/dev/null; then
    skip "kdeconnect"
else
    $PKG kdeconnect 2>/dev/null && ok "kdeconnect installed" || echo "    Not available in repos — install manually"
fi

# ---------------------------------------------------------------------------
# Git config
# ---------------------------------------------------------------------------
step "Git configuration"
git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"
git config --global init.defaultBranch main
git config --global core.autocrlf input
ok "Git configured"

# ---------------------------------------------------------------------------
# GitHub auth
# ---------------------------------------------------------------------------
step "GitHub authentication"
if gh auth status &>/dev/null; then
    skip "already authenticated"
else
    gh auth login
fi

# ---------------------------------------------------------------------------
# Clone repos
# ---------------------------------------------------------------------------
step "Cloning repos to $WORKSPACE"
mkdir -p "$WORKSPACE"
for repo in "${REPOS[@]}"; do
    dest="$WORKSPACE/$repo"
    if [ -d "$dest/.git" ]; then
        skip "$repo"
    else
        echo "    Cloning $GITHUB_USER/$repo..."
        gh repo clone "$GITHUB_USER/$repo" "$dest"
        ok "Cloned $repo"
    fi
done

# ---------------------------------------------------------------------------
# uv sync
# ---------------------------------------------------------------------------
step "uv sync in repos with pyproject.toml"
for repo in "${REPOS[@]}"; do
    pyproject="$WORKSPACE/$repo/pyproject.toml"
    if [ -f "$pyproject" ]; then
        echo "    uv sync: $repo"
        (cd "$WORKSPACE/$repo" && uv sync)
        ok "$repo synced"
    else
        skip "$repo (no pyproject.toml)"
    fi
done

# ---------------------------------------------------------------------------
# Install will plugins into Claude Code
# ---------------------------------------------------------------------------
step "Installing Claude Code plugins"
bash "$WILL_DIR/plugins/install.sh"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo
printf '=%.0s' {1..60}; echo
echo "Bootstrap complete."
echo
echo "Manual steps:"
echo "  [ ] source ~/.bashrc  (or open a new terminal)"
echo "  [ ] Pair KDE Connect: install on Pixel, approve on desktop"
echo "  [ ] Enable USB debugging on phone (Settings > Developer Options)"
echo "  [ ] Install LaTeX for PDF generation: uv run python tools/setup.py  (in health/)"
echo
echo "See will/bootstrap/README.md for full notes."
