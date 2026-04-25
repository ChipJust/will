# Will — System Architecture Plan

*Last updated: 2026-04-25*

This document defines the full multi-repo agent ecosystem Chip is building to manage
life intentionally, with AI assistance across every major context.

---

## Philosophy

Each repo is an **agent** representing a specific life context. Each agent:
- Has its own CLAUDE.md (instructions tailored to that context)
- Accumulates knowledge through ingested references, notes, and data
- Improves through session reflections logged here in `will`
- Operates with the same toolchain conventions for easy portability

The `will` repo is the **meta-agent** — it sees across all contexts and optimizes
the whole system.

**Knowledge is organized as linked nodes.** Small, addressable files connected by
explicit references from indexes. Agents compose context by navigating links, not
by pre-loading the corpus. See `system/context-architecture.md` for the rules and
rationale — this is a foundational design decision that applies to every repo.

---

## Repo Ecosystem

| Repo | Intent | Status | Description |
|------|--------|--------|-------------|
| `will` | Meta / System | Active | This repo. Architecture, reflections, problems, portability. |
| `health` | Health | Active | Personal health research, supplement stack, lab tracking, metrics. |
| `writing` | Writing | Active | Markdown documents written collaboratively with AI. |
| `vibedaw` | Music | Active | Music context agent. Branded name retained. |
| `money` | Personal Finance & Investment | Active | Maximize investment returns while weighing social impact of supported business activity. |
| `giving` | Charitable Giving | Planned | Manage charitable money for the glory of Jesus Christ and love of neighbor. |
| `prayer` | Prayer | Planned | Track prayer requests, prayers offered, and follow-up outcomes. |
| `social-influence` | Social Influence | Planned | Maximize social impact to glorify Jesus Christ through peace, justice, and liberty; influence policy through social media; generates advertising revenue as a side-effect. |

### Naming convention

Private repos use personal shorthand names until they reach a lifecycle point where
a clearer public-facing identity is needed. At that point:
- Map the repo name to an intent name (e.g. rename or create a new public repo), OR
- Let the private intent name remain as part of the internal architecture

`vibedaw` is a precedent: branded name retained because it already has identity.

---

## Personal Layer (`will-personal`)

`will-personal` is the private mirror of this repo. It holds content that
would otherwise belong here but is too sensitive or too personal to commit
publicly. Content categories:

| Category | Path | What it holds |
|----------|------|---------------|
| Reflections | `reflections/YYYY-MM-DD-<repo>.md` | Per-session notes written by `/reflect` |
| Problems | `problems/<topic>.md` | Logged issues blocking the system |
| Hardware | `hardware/machines/<name>.md` | Per-machine spec, purchase, serial, history |
| Hardware projects | `hardware/projects/<name>.md` | Multi-step hardware initiatives (refresh, migration) |
| System | `system/hardware.md`, `system/<other>.md` | Machine spec snapshots and migration notes |
| Config | `config.json` | Personal config (email, etc.) used by tooling |

The wake-up routine (`/wake`) reads `will-personal/HANDOFF.md` as Layer 2 of
its context stack so personal cross-cutting items reach every session.

---

## Cross-Repo Patterns Under Observation

Patterns that have proven out in one repo and may graduate to a system-wide
convention. Track here so promotion is deliberate.

- **Data-intensive repos** (from `money`, 2026-04-19). The pattern is
  `data/holdings/<account>.csv` plus a per-repo `predictions.csv` that
  cross-references external research refs by slug. As more repos accumulate
  structured data, this `data/` + tracking-CSV layout is a candidate for
  formalization.
- **Concept-skills** (from `money`, 2026-04-20). Single markdown files that
  combine human-readable knowledge, tiered model prompts, and a graph-edge
  linkage recipe. Pending v2 corpus-sweep proof; if it works, the format and
  runtime should graduate to `will/plugins/` so other repos (especially
  `health`) can adopt it. See `system/docs-as-inputs.md` for the
  architectural principle this depends on.
- **Hardware tracking** (from `will-personal`, 2026-04-12). Per-machine
  files in `hardware/machines/`, multi-step initiatives in
  `hardware/projects/`. Already in use; documented above as the canonical
  layout.

---

## Reflection Workflow

**Rule:** Run `/reflect` at the end of every session in any repo.

The `/reflect` skill:
1. Summarizes what was built or decided
2. Captures what worked, what didn't, and what to do differently
3. Writes a dated file to `will-personal/reflections/YYYY-MM-DD-<repo>.md`
4. Updates memory files in `~/.claude/projects/<project>/memory/` as needed
5. Suggests updates to CLAUDE.md or skill files if the session revealed gaps

Reflections accumulate into a knowledge base that future sessions can read to
re-establish context quickly after long gaps.

---

## Portability

**Current machine:** Windows 10 Pro (D:\_code\ workspace)
**Machine spec:** See `will-personal/system/hardware.md` — i9-9960X, 128GB RAM, ASRock X299 Steel Legend.

**Known portability problem:** Windows does not support Chip's target hardware.
See `will-personal/problems/windows-hardware.md`. Linux migration is the recommended path.

**Bootstrap:** Run `bootstrap/setup.sh` (Linux) or `bootstrap/setup.ps1` (Windows)
from the will repo. One command installs all tools, clones all repos, runs uv sync.

**Critical thing to port:** `~/.claude/` — contains all plugins, memory, and settings.
This directory must be backed up or re-built on any new machine.

**Planned Linux migration:** See `system/hardware.md` for dual-boot approach and
distro recommendation (Ubuntu 24.04 LTS). Machine is fully compatible with Linux.

---

## Open Problems

See `will-personal/problems/`. Current:
- `windows-hardware.md` — OS does not support target hardware; machine migration needed

---

## Planned Repos — Next Steps

### `giving`
- Track donations, recipients, amounts, dates
- Research causes and organizations
- Hold theological notes on stewardship
- Eventual: reporting for tax purposes

### `prayer`
- Log prayer requests with date, person/situation, context
- Record when prayer was offered
- Track follow-up outcomes (answered, ongoing, unknown)
- Private by default; no identifying information in commits

### `social-influence`
- Research on effective advocacy and policy influence
- Social media content strategy grounded in Christian ethics
- Track platform analytics and content performance
- Revenue stream via advertising treated as a means, not an end

---

## System Conventions (All Repos)

- **Branch:** `main` always, never `master`
- **Package manager:** `uv` only, never `pip` or `pipx`
- **Commit style:** "commit" = stage + commit + push all agent-modified files, no prompts
- **PDF generation:** `tools/convert.py` via pypandoc/xelatex (where applicable)
- **Research ingest:** `tools/ingest.py` → `research/refs/` (health repo pattern; portable to others)
- **Memory:** `~/.claude/projects/<project>/memory/` — persists across sessions
- **Skills:** `~/.claude/plugins/marketplaces/will-plugins/plugins/` (will repo skills)
- **Claude Code permissions:** Three-tier — user-global, per-repo committed, per-repo local (gitignored). CLAUDE.md is not a permission surface; only `settings.json` is. Full writeup at `system/permissions.md`.

---

## Revision History

| Date | Change |
|------|--------|
| 2026-04-06 | Initial creation; ecosystem defined; first session reflection (health) |
| 2026-04-06 | Added money repo; UTF-8 fix applied to all PDF/VTT extractors |
| 2026-04-06 | Added hardware spec, bootstrap scripts, system conventions, AI hardware research |
| 2026-04-08 | Fix stale paths (will-personal refs); fix bootstrap description in ORIENTATION.md |
| 2026-04-19 | Add three-tier Claude Code permission convention to System Conventions; deployed across all 7 active repos |
| 2026-04-25 | Add Personal Layer + Cross-Repo Patterns sections; full permission convention writeup at `system/permissions.md`; "docs as inputs, graph as overlay" principle at `system/docs-as-inputs.md` |
