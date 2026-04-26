# Agent Scheduling — Cohort Coordination via Chat

Multi-context scheduling platform where each participant's personal agent negotiates meeting times with the others' agents, optimizing across batches of interrelated meetings, and surfacing to the human only via the resulting calendar invite.

The cohort use case is the first instance — seven members, one full-cohort meeting per month plus triad meetings — but the system is designed for general groups (cohort, marriage, work circles, …). See `02-requirements.md` for the full scope.

Originally drafted as a problem note 2026-04-22; migrated into the projects template 2026-04-26; requirements/spec/design resolved 2026-04-26 with all ADRs (0001–0007) Accepted. **Prototype target: Jun 1, 2026.**

## Quick links

- [STATUS.md](STATUS.md) — current phase and next action
- [01-research.md](01-research.md) — skipped, with conditions for re-opening
- [02-requirements.md](02-requirements.md)
- [03-specification.md](03-specification.md)
- [04-design.md](04-design.md)
- [05-implementation.md](05-implementation.md) — TDD slice list driving the build
- [decisions/](decisions/) — ADRs 0001–0007 (all Accepted)
- [code/](code/) — Python package skeleton

## How to engage

Read STATUS.md first. If you're picking this up to build, start at `05-implementation.md` slice 1. Do not change `02`/`03`/`04` mid-build — if you find the spec or design wrong, stop and fix the upstream document explicitly, then continue.

## Note on repo location

Lives at `will/projects/agent-scheduling/` for the planning and prototype phases. Graduates to its own repo (provisional name placeholder: `convene`) when the application ships, or earlier if `will`'s scope as Chip's meta-agent vs. a multi-user platform forces the split. See the closing section of `02-requirements.md`.
