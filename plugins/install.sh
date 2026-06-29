#!/usr/bin/env bash
# Install will repo plugins into Claude Code via the marketplace CLI.
# Run from the will repo root: bash plugins/install.sh
#
# Structure expected by Claude Code:
#   <marketplace_root>/.claude-plugin/marketplace.json   <- manifest at REPO ROOT
#   <marketplace_root>/plugins/<name>/                   <- plugin dirs
#
# That means marketplace root = D:\_code\will (the repo root, not plugins/).

set -euo pipefail

WILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Registering will-plugins marketplace (root: $WILL_DIR)"

# Remove stale entry if present (ignore errors)
claude plugins marketplace remove will-plugins 2>/dev/null || true

# Re-add pointing at the repo root where .claude-plugin/marketplace.json lives
claude plugins marketplace add "$WILL_DIR"

echo "==> Installing plugins"
claude plugins install reflect
claude plugins install commit-push
claude plugins install ingest 2>/dev/null || echo "    (ingest skipped — may not be listed yet)"
claude plugins install phone 2>/dev/null || echo "    (phone skipped — may not be listed yet)"
# Clean up retired plugins (silent if not installed).
claude plugins uninstall health-ingest 2>/dev/null || true
claude plugins uninstall wake 2>/dev/null || true

echo "==> Done. Restart Claude Code to pick up the new skills."
