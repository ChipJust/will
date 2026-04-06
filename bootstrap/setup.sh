#!/usr/bin/env bash
# Bootstrap Chip's development workstation on Linux (Ubuntu/Debian primary target).
# Run from the will repo root, or pipe directly:
#   bash <(curl -sL https://raw.githubusercontent.com/ChipJust/will/main/bootstrap/setup.sh)

set -euo pipefail

WORKSPACE="$HOME/code"
GIT_USER_NAME="Chip Ueltschey"
GIT_USER_EMAIL="chip@chipjust.com"   # update if email changes
GITHUB_USER="ChipJust"

REPOS=(
    will
    health
    writing
    vibedaw
    money
    # Add: giving prayer social-influence when created
)

step()  { echo; echo "==> $*"; }
ok()    { echo "    OK: $*"; }
skip()  { echo "    --: $* (already done)"; }

# ---------------------------------------------------------------------------
# Detect distro
# ---------------------------------------------------------------------------
if command -v apt-get &>/dev/null; then
    PKG_INSTALL="sudo apt-get install -y"
    PKG_UPDATE="sudo apt-get update"
elif command -v dnf &>/dev/null; then
    PKG_INSTALL="sudo dnf install -y"
    PKG_UPDATE="sudo dnf check-update || true"
elif command -v brew &>/dev/null; then
    PKG_INSTALL="brew install"
    PKG_UPDATE="brew update"
else
    echo "Unsupported package manager. Install git, gh, node, curl manually then re-run."
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
step "Updating package index"
$PKG_UPDATE

step "Installing system packages"
$PKG_INSTALL git curl wget build-essential libssl-dev

# ---------------------------------------------------------------------------
# 2. GitHub CLI
# ---------------------------------------------------------------------------
step "Installing GitHub CLI"
if command -v gh &>/dev/null; then
    skip "gh"
else
    # Ubuntu/Debian path
    if command -v apt-get &>/dev/null; then
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
            | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
            https://cli.github.com/packages stable main" \
            | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt-get update && sudo apt-get install gh -y
    else
        $PKG_INSTALL gh
    fi
    ok "gh installed"
fi

# ---------------------------------------------------------------------------
# 3. Node.js (LTS via nvm)
# ---------------------------------------------------------------------------
step "Installing Node.js via nvm"
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
# 4. uv
# ---------------------------------------------------------------------------
step "Installing uv"
if command -v uv &>/dev/null; then
    skip "uv $(uv --version)"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    ok "uv installed"
fi

# ---------------------------------------------------------------------------
# 5. Claude Code
# ---------------------------------------------------------------------------
step "Installing Claude Code"
if command -v claude &>/dev/null; then
    skip "claude already installed"
else
    npm install -g @anthropic-ai/claude-code
    ok "Claude Code installed"
fi

# ---------------------------------------------------------------------------
# 6. Android platform-tools (adb)
# ---------------------------------------------------------------------------
step "Installing Android platform-tools (adb)"
if command -v adb &>/dev/null; then
    skip "adb"
else
    $PKG_INSTALL android-tools-adb 2>/dev/null || {
        echo "    Falling back to manual install..."
        ADB_ZIP="platform-tools-latest-linux.zip"
        curl -O "https://dl.google.com/android/repository/$ADB_ZIP"
        unzip -q "$ADB_ZIP" -d "$HOME"
        rm "$ADB_ZIP"
        echo "export PATH=\"\$HOME/platform-tools:\$PATH\"" >> "$HOME/.bashrc"
        export PATH="$HOME/platform-tools:$PATH"
    }
    ok "adb installed"
fi

# ---------------------------------------------------------------------------
# 7. KDE Connect (Linux desktop ↔ Pixel 7)
# ---------------------------------------------------------------------------
step "Installing KDE Connect"
if command -v kdeconnect-cli &>/dev/null; then
    skip "kdeconnect already installed"
else
    $PKG_INSTALL kdeconnect || echo "    KDE Connect not available in repos; install manually"
fi

# ---------------------------------------------------------------------------
# 8. Git configuration
# ---------------------------------------------------------------------------
step "Configuring Git"
git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"
git config --global init.defaultBranch main
git config --global core.autocrlf input
ok "Git configured for $GIT_USER_NAME"

# ---------------------------------------------------------------------------
# 9. GitHub authentication
# ---------------------------------------------------------------------------
step "GitHub CLI authentication"
if gh auth status &>/dev/null; then
    skip "already authenticated"
else
    echo "    Launching interactive GitHub login..."
    gh auth login
fi

# ---------------------------------------------------------------------------
# 10. Clone repos
# ---------------------------------------------------------------------------
step "Cloning repos to $WORKSPACE"
mkdir -p "$WORKSPACE"

for repo in "${REPOS[@]}"; do
    dest="$WORKSPACE/$repo"
    if [ -d "$dest/.git" ]; then
        skip "$repo already cloned"
    else
        echo "    Cloning $GITHUB_USER/$repo..."
        gh repo clone "$GITHUB_USER/$repo" "$dest"
        ok "Cloned $repo"
    fi
done

# ---------------------------------------------------------------------------
# 11. uv sync in each repo
# ---------------------------------------------------------------------------
step "Running uv sync in repos with pyproject.toml"
for repo in "${REPOS[@]}"; do
    pyproject="$WORKSPACE/$repo/pyproject.toml"
    if [ -f "$pyproject" ]; then
        echo "    uv sync: $repo..."
        (cd "$WORKSPACE/$repo" && uv sync)
        ok "$repo synced"
    else
        skip "$repo (no pyproject.toml)"
    fi
done

# ---------------------------------------------------------------------------
# 12. Post-setup checklist
# ---------------------------------------------------------------------------
echo
echo "$(printf '=%.0s' {1..60})"
echo "Bootstrap complete. Manual steps remaining:"
echo ""
echo "  [ ] Pair KDE Connect: open app on Pixel 7, approve on desktop"
echo "  [ ] Enable ADB on Pixel 7: Settings > Developer Options > USB Debugging"
echo "  [ ] Verify ingest: uv run python tools/ingest.py --help  (in health/ or money/)"
echo "  [ ] Install LaTeX for PDF generation: uv run python tools/setup.py  (in health/)"
echo "  [ ] Reload shell: source ~/.bashrc (or open new terminal)"
echo ""
echo "See will/bootstrap/README.md for full post-setup notes."
