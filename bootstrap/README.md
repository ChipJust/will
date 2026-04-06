# Bootstrap — One-Step Workstation Setup

Run a single script from the will repo to configure any machine as Chip's
development workstation. The script detects the OS and handles the rest.

## Usage

### Windows (PowerShell, run as Administrator)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\bootstrap\setup.ps1
```

### Linux
```bash
bash bootstrap/setup.sh
```

## What it does

1. Installs system package manager if needed (winget, apt, brew)
2. Installs core tools: git, gh, uv, Node.js, Claude Code, Android platform-tools
3. Authenticates GitHub CLI (`gh auth login` — interactive)
4. Clones all ChipJust repos to the workspace directory
5. Runs `uv sync` in each repo that has a `pyproject.toml`
6. Installs Claude Code global plugins (will repo contains plugin definitions)
7. Prints a post-setup checklist

## Workspace layout

All repos clone to a single workspace directory:
- **Windows:** `D:\_code\`
- **Linux:** `~/code/`

## Post-setup (manual steps)

- [ ] Configure Git signing if desired
- [ ] Run `gh auth login` and select SSH
- [ ] Install KDE Connect on both desktop and Pixel 7
- [ ] Set up Syncthing if folder sync is needed
- [ ] Install any AI model weights to the models directory
- [ ] Verify `uv run python tools/ingest.py` works in health and money repos

## Adding new tools to bootstrap

Edit `setup.ps1` or `setup.sh` and add to the relevant install block.
Both scripts are idempotent — safe to re-run.
