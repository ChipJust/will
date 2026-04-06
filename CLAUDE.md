# will

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
- `reflections/` — dated session notes; run `/reflect` at the end of every session
- `problems/` — logged issues blocking the system
- `system/` — repo ecosystem definition and conventions

## Working here

- Branch: `main`
- Use `/reflect` at the end of any session (in any repo) to write a reflection here
- When you solve a problem in `problems/`, mark it resolved with date and close notes
- Keep PLAN.md current — it is the source of truth for what the system is and where it's going

## Tools

- **Package manager:** `uv` (if/when tooling is added)
- **GitHub CLI:** `gh` authenticated as ChipJust

## Conventions

- Reflections are named `YYYY-MM-DD-<repo>.md` (e.g. `2026-04-06-health.md`)
- Problems are named by topic (e.g. `windows-hardware.md`)
- No code lives here — this is a planning and reflection repo
