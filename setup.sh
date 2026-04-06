#!/usr/bin/env bash
# Minimal first-time setup for the will system.
# Installs only what is needed to run Claude Code, then exits.
# Claude handles everything else.
#
# Usage: bash setup.sh

set -euo pipefail

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
RESET="\033[0m"

step() { echo -e "\n${CYAN}==> $*${RESET}"; }
ok()   { echo -e "${GREEN}    ok: $*${RESET}"; }
skip() { echo    "    --: $* (already installed)"; }

echo -e "${BOLD}"
echo "  will — system setup"
echo "  Installing prerequisites for Claude Code..."
echo -e "${RESET}"

# ---------------------------------------------------------------------------
# Detect package manager
# ---------------------------------------------------------------------------
if command -v apt-get &>/dev/null; then
    PKG_UPDATE="sudo apt-get update -qq"
    PKG="sudo apt-get install -y"
elif command -v dnf &>/dev/null; then
    PKG_UPDATE="true"
    PKG="sudo dnf install -y"
elif command -v brew &>/dev/null; then
    PKG_UPDATE="brew update"
    PKG="brew install"
else
    echo "ERROR: No supported package manager (apt, dnf, brew)." >&2
    echo "Install git, curl, and Node.js manually, then re-run." >&2
    exit 1
fi

$PKG_UPDATE

# ---------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------
step "git"
if command -v git &>/dev/null; then
    skip "git $(git --version | awk '{print $3}')"
else
    $PKG git
    ok "git installed"
fi

# ---------------------------------------------------------------------------
# curl
# ---------------------------------------------------------------------------
step "curl"
if command -v curl &>/dev/null; then
    skip "curl"
else
    $PKG curl
    ok "curl installed"
fi

# ---------------------------------------------------------------------------
# Node.js (required for Claude Code)
# ---------------------------------------------------------------------------
step "Node.js"
if command -v node &>/dev/null; then
    skip "node $(node --version)"
else
    if command -v apt-get &>/dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif command -v dnf &>/dev/null; then
        $PKG nodejs npm
    else
        brew install node
    fi
    ok "node $(node --version)"
fi

# ---------------------------------------------------------------------------
# uv (Python package manager used by all repos)
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
    skip "claude"
else
    npm install -g @anthropic-ai/claude-code
    ok "Claude Code installed"
fi

# ---------------------------------------------------------------------------
# Done — hand off to Claude
# ---------------------------------------------------------------------------
WILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo
echo -e "  Prerequisites installed. ${BOLD}Do not launch Claude yet.${RESET}"
echo
echo "  If your terminal needs a restart to pick up new PATH entries:"
echo "    source ~/.bashrc   (or open a new terminal)"
echo
echo "  Then, from this directory, run:"
echo
echo -e "    ${BOLD}${CYAN}claude${RESET}"
echo
echo "  Claude will read SETUP.md and walk you through the rest."
echo
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
