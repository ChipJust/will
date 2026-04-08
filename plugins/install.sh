#!/usr/bin/env bash
# Install will repo plugins into Claude Code's plugin directory.
# Run from the will repo root: bash plugins/install.sh

set -euo pipefail

WILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_MARKETPLACE="$HOME/.claude/plugins/marketplaces/will-plugins"
CLAUDE_PLUGINS="$CLAUDE_MARKETPLACE/plugins"
KNOWN_MARKETPLACES="$HOME/.claude/plugins/known_marketplaces.json"

echo "==> Installing will plugins to $CLAUDE_PLUGINS"
mkdir -p "$CLAUDE_PLUGINS"

# Copy marketplace manifest so Claude Code recognises this as a valid marketplace
mkdir -p "$CLAUDE_MARKETPLACE/.claude-plugin"
cp "$WILL_DIR/plugins/.claude-plugin/marketplace.json" "$CLAUDE_MARKETPLACE/.claude-plugin/marketplace.json"
echo "    Installed marketplace.json"

# Copy each plugin directory
for plugin_dir in "$WILL_DIR/plugins"/*/; do
    plugin_name="$(basename "$plugin_dir")"
    [[ "$plugin_name" == "install.sh" || "$plugin_name" == "install.ps1" || "$plugin_name" == ".claude-plugin" ]] && continue
    echo "    Installing plugin: $plugin_name"
    rm -rf "$CLAUDE_PLUGINS/$plugin_name"
    cp -r "$plugin_dir" "$CLAUDE_PLUGINS/$plugin_name"
done

# Register will-plugins marketplace in known_marketplaces.json
# installLocation must point to the marketplace root (e.g. .../will-plugins),
# NOT the plugins subdirectory — the system appends /plugins/ itself.
if [ -f "$KNOWN_MARKETPLACES" ]; then
    # Convert Unix-style paths to Windows paths for Python on Windows
    WIN_MARKETPLACES="$(cygpath -w "$KNOWN_MARKETPLACES" 2>/dev/null || echo "$KNOWN_MARKETPLACES")"
    WIN_WILL_PLUGINS="$(cygpath -w "$WILL_DIR/plugins" 2>/dev/null || echo "$WILL_DIR/plugins")"
    WIN_CLAUDE_MARKETPLACE="$(cygpath -w "$CLAUDE_MARKETPLACE" 2>/dev/null || echo "$CLAUDE_MARKETPLACE")"
    python - <<PYEOF
import json
with open(r"$WIN_MARKETPLACES") as f:
    data = json.load(f)
data["will-plugins"] = {
    "source": {"source": "local", "path": r"$WIN_WILL_PLUGINS"},
    "installLocation": r"$WIN_CLAUDE_MARKETPLACE",
    "lastUpdated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
with open(r"$WIN_MARKETPLACES", "w") as f:
    json.dump(data, f, indent=2)
print("    Registered will-plugins marketplace")
PYEOF
fi

echo "==> Plugins installed. Restart Claude Code to pick them up."
