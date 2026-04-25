# Claude Code Permissions — Three-Tier Convention

How Claude Code's permission allow-lists are organized across this ecosystem so
that workflows run without prompts, while local edits stay private and
agent-organic entries don't contaminate the committed repo.

**See also:** `conventions.md` for general working style.

---

## The three tiers

| Tier | Path | Purpose | Committed? |
|------|------|---------|------------|
| 1. User-global | `~/.claude/settings.json` | Safe cross-repo commands available everywhere | Personal — outside any repo |
| 2. Per-repo committed | `<repo>/.claude/settings.json` | Curated workflow allow-list for this repo | Yes |
| 3. Per-repo local | `<repo>/.claude/settings.local.json` | Organic personal overrides while working | No (gitignored) |

Permissions resolve as the union across all three tiers. A command allowed at
any tier runs without prompting.

## What goes where

**Tier 1 (`~/.claude/settings.json`)** — commands approved on every machine,
in every repo. Examples: `Bash(git status:*)`, `Bash(ls:*)`, `Bash(uv:*)`,
`Bash(gh pr list:*)`. Read-only or universally safe.

**Tier 2 (`<repo>/.claude/settings.json`)** — workflows specific to this repo.
Examples in the will repo: `Bash(uv run python tools/:*)`,
`Bash(bash plugins/install.sh:*)`. Curated by hand; this is what gets reviewed
in PRs.

**Tier 3 (`<repo>/.claude/settings.local.json`)** — auto-populated by Claude
Code as you click "Always allow" during work. Stays out of git. Periodically
review and either promote useful entries up to Tier 1 or 2, or leave them
local.

## Pattern A vs Pattern B

**Pattern A — tool-specific:** `Bash(uv run python tools/statusline.py:*)`
- Tight scope, audit-friendly
- Must add an entry every time a new script appears
- Use when targets need explicit review

**Pattern B — directory-prefix wildcard:** `Bash(uv run python tools/:*)`
- Zero-maintenance — any script under that directory is pre-approved
- Broader trust scope (anything with that prefix runs)
- Use when directory contents are all trusted by construction (your own tools)

This ecosystem uses Pattern B for tool directories (`tools/`) and Pattern A
only when narrower scope is genuinely needed.

## CLAUDE.md is not a permission surface

CLAUDE.md is loaded as model context — it tells Claude *how* to behave.
Permissions are enforced by the Claude Code harness, which only reads
`settings.json`. Putting "you may run X" in CLAUDE.md does nothing at the
enforcement layer; the model may follow the instruction but the harness still
prompts.

Rule: every pre-approval lives in a `settings.json` file. CLAUDE.md is for
preferences, conventions, and context — never permissions.

## .gitignore whitelist pattern

Each repo's `.gitignore` uses the whitelist form so committed settings ship
while local settings stay out:

```
.claude/*
!.claude/settings.json
```

This commits the curated Tier 2 file and ignores everything else (plugins,
projects state, `settings.local.json`).

## Migrating entries between tiers

- **Tier 3 → Tier 2:** local entry has proven useful and is repo-specific
- **Tier 3 → Tier 1:** entry is safe and applies across all repos
- **Tier 2 → Tier 1:** a per-repo entry turns out to be universally useful
- **Tier 1 → Tier 2:** an entry is too broad and should be repo-scoped

After moving an entry up, delete it from the lower tier so the source of
truth stays clear.
