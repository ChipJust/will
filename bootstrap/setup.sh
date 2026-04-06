#!/usr/bin/env bash
# Bootstrap a workstation from the will repo.
# Run from the will repo root: bash bootstrap/setup.sh
#
# Phase 1: install git + gh, authenticate with GitHub
# Phase 2: clone will-personal to get config.json
# Phase 3: install everything else using config

set -euo pipefail

WILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

step()  { echo; echo "==> $*"; }
ok()    { echo "    OK: $*"; }
skip()  { echo "    --: $* (already done)"; }
die()   { echo "ERROR: $*" >&2; exit 1; }

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
    die "No supported package manager (apt, dnf, brew)."
fi

# ===========================================================================
# PHASE 1 — Minimal install: git + gh + authenticate
# ===========================================================================

step "[Phase 1] git"
if command -v git &>/dev/null; then
    skip "git"
else
    $PKG git
    ok "git installed"
fi

step "[Phase 1] GitHub CLI"
if command -v gh &>/dev/null; then
    skip "gh"
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

step "[Phase 1] GitHub authentication"
if gh auth status &>/dev/null; then
    skip "already authenticated"
else
    gh auth login
fi

GITHUB_USER=$(gh api user -q .login)
ok "Authenticated as: $GITHUB_USER"

# ===========================================================================
# PHASE 2 — Clone will-personal, read config
# ===========================================================================

step "[Phase 2] Locating will-personal"

# Determine workspace: try to read from existing config, else default
PERSONAL_REPO="${GITHUB_USER}/will-personal"
DEFAULT_WORKSPACE="$HOME/code"

# Check if will-personal exists for this user
if gh repo view "$PERSONAL_REPO" &>/dev/null 2>&1; then
    ok "Found $PERSONAL_REPO"
    PERSONAL_DIR="$DEFAULT_WORKSPACE/will-personal"
    if [ ! -d "$PERSONAL_DIR/.git" ]; then
        mkdir -p "$DEFAULT_WORKSPACE"
        gh repo clone "$PERSONAL_REPO" "$PERSONAL_DIR"
        ok "Cloned will-personal"
    else
        skip "will-personal already cloned"
    fi
    CONFIG="$PERSONAL_DIR/config.json"
else
    echo "    $PERSONAL_REPO not found on GitHub."
    echo "    Creating it from will/config.example.json..."
    cp "$WILL_DIR/config.example.json" "$WILL_DIR/config.json"
    echo
    echo "    *** ACTION REQUIRED ***"
    echo "    Edit $WILL_DIR/config.json with your details, then re-run this script."
    echo "    After filling it in, the script will create will-personal for you."
    exit 0
fi

# Read config
[ -f "$CONFIG" ] || die "config.json not found in will-personal."
GIT_NAME=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(d['git']['name'])")
GIT_EMAIL=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(d['git']['email'])")
WORKSPACE=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(d['workspace']['linux'])")
WORKSPACE="${WORKSPACE/#\~/$HOME}"
REPOS=$(python3 -c "import json; d=json.load(open('$CONFIG')); print(' '.join(d['repos']))")
read -ra REPOS <<< "$REPOS"

ok "Config loaded: $GIT_NAME | workspace: $WORKSPACE"

# ===========================================================================
# PHASE 3 — Full install
# ===========================================================================

step "[Phase 3] Node.js (via nvm)"
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

step "[Phase 3] uv"
if command -v uv &>/dev/null; then
    skip "uv $(uv --version)"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    ok "uv installed"
fi

step "[Phase 3] Claude Code"
if command -v claude &>/dev/null; then
    skip "claude"
else
    npm install -g @anthropic-ai/claude-code
    ok "Claude Code installed"
fi

step "[Phase 3] ADB (Android platform-tools)"
if command -v adb &>/dev/null; then
    skip "adb"
else
    $PKG android-tools-adb 2>/dev/null || {
        curl -O "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
        unzip -q platform-tools-latest-linux.zip -d "$HOME"
        rm platform-tools-latest-linux.zip
        echo "export PATH=\"\$HOME/platform-tools:\$PATH\"" >> "$HOME/.bashrc"
        export PATH="$HOME/platform-tools:$PATH"
    }
    ok "adb ready"
fi

step "[Phase 3] KDE Connect"
if command -v kdeconnect-cli &>/dev/null; then
    skip "kdeconnect"
else
    $PKG kdeconnect 2>/dev/null && ok "kdeconnect installed" || echo "    Not in repos — install manually"
fi

step "[Phase 3] Git configuration"
git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"
git config --global init.defaultBranch main
git config --global core.autocrlf input
ok "Git configured"

step "[Phase 3] Cloning repos to $WORKSPACE"
mkdir -p "$WORKSPACE"
for repo in "${REPOS[@]}"; do
    dest="$WORKSPACE/$repo"
    if [ -d "$dest/.git" ]; then
        skip "$repo"
    else
        gh repo clone "$GITHUB_USER/$repo" "$dest"
        ok "Cloned $repo"
    fi
done

step "[Phase 3] uv sync"
for repo in "${REPOS[@]}"; do
    if [ -f "$WORKSPACE/$repo/pyproject.toml" ]; then
        (cd "$WORKSPACE/$repo" && uv sync)
        ok "$repo synced"
    else
        skip "$repo (no pyproject.toml)"
    fi
done

step "[Phase 3] Installing Claude Code plugins"
bash "$WILL_DIR/plugins/install.sh"

# ---------------------------------------------------------------------------
echo
printf '=%.0s' {1..60}; echo
echo "Bootstrap complete."
echo
echo "Manual steps:"
echo "  [ ] source ~/.bashrc  (or open new terminal)"
echo "  [ ] Pair KDE Connect on phone"
echo "  [ ] Enable USB debugging on phone"
echo "  [ ] Install LaTeX: uv run python tools/setup.py  (in health/)"
echo
echo "See will/bootstrap/README.md for full notes."
