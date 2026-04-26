# will

## First-time setup?

If `will-personal` has not been cloned and no repos beyond `will` are present on
this machine, this is a fresh install. Read `SETUP.md` and follow its instructions
— introduce yourself as the setup agent and ask permission before doing anything.

---

Meta-agent repo. This is the operating system for Chip's life — it defines the full
multi-repo agent ecosystem, tracks open problems, and improves itself through session
reflections.

## Purpose

Every other repo is a context agent (health, music, writing, etc.). This repo is the
agent that manages all of them. It holds:
- The architecture plan for the whole system
- Session reflections and learnings (one file per session)
- Logged problems that need resolution
- System-wide conventions and portability notes

## Key files

- `PLAN.md` — master architecture; start here
- `projects/` — software projects developed in `will`; each has a 5-phase template (research → requirements → spec → design → implementation)
- `reflections/` — dated session notes; run `/reflect` at the end of every session
- `system/` — repo ecosystem definition and conventions

Personal/operational issues (windows-hardware, etc.) live in `will-personal/problems/`, not here. `projects/` is the public, collaborator-facing surface for software work.

## Session start (wake-up routine)

Before doing anything else in a new session:
1. Read `HANDOFF.md` — current system state, cross-cutting concerns, open items
2. Read `ORIENTATION.md` — what lives here and design principles
3. Read `PLAN.md` — master architecture if doing structural work

Or just run `/wake` and it handles all of this.

## Working here

- Branch: `main`
- Use `/reflect` at the end of any session (in any repo) to write a reflection here
- New software project? Start with `cp -r projects/_template/ projects/<name>/` and walk through the phase files. The template is a maximum, not a minimum — skip phases that don't add value, leaving a one-line note in the saved response saying why.
- Keep PLAN.md current — it is the source of truth for what the system is and where it's going

## Tools

- **Package manager:** `uv` (if/when tooling is added)
- **GitHub CLI:** `gh` authenticated as ChipJust

## tools/

Cross-repo Python scripts and utilities — tools that skills call, and scripts that need
to work across all repos (health, money, writing, etc.). This is the one place in this
repo where executable code lives. Every topic repo also has a `tools/` directory with
its own per-repo scripts; the convention is consistent.

- `statusline.py` — Claude Code status line, registered in `~/.claude/settings.json`
- `commit_push.py` — staged + commit + push as a single approved CLI call
- Each script documents its expected input and output in its module docstring (sample
  JSON in, sample string out). Read the docstring before writing any parsing code.

## Conventions

- Reflections are named `YYYY-MM-DD-<repo>.md` (e.g. `2026-04-06-health.md`)
- Projects are named by topic, kebab-case (e.g. `agent-scheduling/`); each follows the 5-phase template at `projects/_template/`
- Problems (personal/operational) are named by topic and live in `will-personal/problems/` (e.g. `windows-hardware.md`)
