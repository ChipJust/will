# will — Agent Orientation

Read this before proposing to build anything in this repo.

---

## What this repo is

`will` is the **public framework** — the infrastructure that makes the whole
multi-repo agent ecosystem work. It holds:
- Plugin/skill definitions for Claude Code
- Bootstrap scripts for new machine setup
- System-wide conventions

Personal content (reflections, problems, config) lives in `will-personal` (private).

---

## What exists

### Plugins (`plugins/`)

Each subdirectory is a Claude Code plugin. Installed via `bash plugins/install.sh`.

| Plugin | Skill | Purpose |
|--------|-------|---------|
| `reflect` | `/reflect` | End-of-session reflection; writes to will-personal/reflections/ |
| `wake` | `/wake` | Session-start review; reads HANDOFF.md + will context, briefs agent |
| `health-ingest` | `/ingest-paper` | Research paper ingest fallback decision tree |

**Do not add logic directly to install.sh.** Plugin structure is: `plugins/<name>/skills/<skill>/SKILL.md`.
Adding a new skill = new directory following that pattern, then re-run install.sh.

### Bootstrap (`bootstrap/`)

- `setup.sh` — Linux/Mac: 3-phase full bootstrap (install tools, authenticate GitHub,
  clone repos, configure git, install plugins)
- `setup.ps1` — Windows: same
- `README.md` — usage notes and post-setup checklist

The root `setup.sh` / `setup.bat` are the *minimal* first-run scripts (prereqs only).
The setup agent (`SETUP.md`) runs the bootstrap scripts as its execution engine
after Claude Code is installed.

### System conventions (`system/conventions.md`)

Canonical source for system-wide rules: branch naming, package manager (uv), commit
style, encoding requirements, etc. Any new convention goes here first.

### PLAN.md

Master architecture. Source of truth for the repo ecosystem. Keep it current.

---

## Relationship to will-personal

| will (this repo) | will-personal |
|------------------|---------------|
| Public | Private |
| Framework | Personal instance |
| Plugins, bootstrap, conventions | Config, reflections, problems, hardware |
| Anyone can fork | Never shared |

Bootstrap discovers will-personal from GitHub auth (`gh api user`), clones it,
reads `config.json`, drives the rest of setup.

---

## Design principles

**Skills over scripts.** Behavior that Claude should execute lives in SKILL.md files,
not in shell scripts. Scripts are for mechanical install steps only.

**Public/private split is strict.** Nothing personal (names, emails, machine specs,
reflections) ever goes into will. It always goes into will-personal.

**will is the OS; subject repos are apps.** Changes here affect every repo's workflow.
Be conservative. When in doubt, put new things in a subject repo first.

---

## Before adding a new plugin or skill

1. Read an existing SKILL.md to understand the format
2. Check if an existing skill can be extended rather than a new one added
3. New plugin = new directory under `plugins/`, run install.sh to deploy
