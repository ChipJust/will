#!/usr/bin/env bash
# Stage 0 for the will system — the only shell in the bootstrap path.
#
# Its entire job is to guarantee git and python3 exist, then hand off to
# bootstrap/bootstrap.py, which does the real work in Python. Everything that
# used to live here (Node via NodeSource, uv via a piped installer, Claude Code)
# moved into bootstrap.py so there is exactly one implementation of each step.
#
# Usage: bash setup.sh

set -euo pipefail

BOLD="\033[1m"; CYAN="\033[36m"; GREEN="\033[32m"; RESET="\033[0m"
step() { echo -e "\n${CYAN}==> $*${RESET}"; }
ok()   { echo -e "${GREEN}    ok: $*${RESET}"; }
skip() { echo    "    --: $* (already present)"; }

echo -e "${BOLD}"
echo "  will — stage 0"
echo "  Ensuring git and python3, then handing off to bootstrap.py"
echo -e "${RESET}"

if command -v apt-get &>/dev/null; then
    PKG="sudo apt-get install -y -q"
    sudo apt-get update -qq
elif command -v dnf &>/dev/null; then
    PKG="sudo dnf install -y"
elif command -v brew &>/dev/null; then
    PKG="brew install"
else
    echo "ERROR: no supported package manager (apt, dnf, brew)." >&2
    echo "Install git and python3 manually, then run:" >&2
    echo "  python3 bootstrap/bootstrap.py" >&2
    exit 1
fi

step "git"
if command -v git &>/dev/null; then
    skip "git $(git --version | awk '{print $3}')"
else
    $PKG git
    ok "git installed"
fi

step "python3"
if command -v python3 &>/dev/null; then
    skip "python3 $(python3 --version | awk '{print $2}')"
else
    $PKG python3
    ok "python3 installed"
fi

WILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo
echo -e "${BOLD}────────────────────────────────────────────────────────────${RESET}"
echo
echo "  Stage 0 done. Now run the Python bootstrap — it previews"
echo "  everything first and changes nothing until you pass --execute:"
echo
echo -e "    ${BOLD}${CYAN}python3 ${WILL_DIR}/bootstrap/bootstrap.py${RESET}"
echo
echo "  Then, to apply:"
echo
echo -e "    ${BOLD}${CYAN}python3 ${WILL_DIR}/bootstrap/bootstrap.py --execute${RESET}"
echo
echo "  That installs gh, Node, uv and Claude Code, authenticates GitHub,"
echo "  clones your repos and installs plugins. Afterwards:"
echo
echo "    python3 bootstrap/harden.py      # security posture"
echo "    python3 bootstrap/restore.py     # staged data off the old drive"
echo
echo -e "${BOLD}────────────────────────────────────────────────────────────${RESET}"
