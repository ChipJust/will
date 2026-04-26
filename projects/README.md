# projects/

Software projects developed in `will`. Each project sits in its own directory and follows a 5-phase lifecycle.

## Phases

| # | File | Purpose |
|---|------|---------|
| 01 | `01-research.md` | Prior art, constraints, open variables |
| 02 | `02-requirements.md` | Who, what, success criteria, non-goals |
| 03 | `03-specification.md` | Externally observable behavior |
| 04 | `04-design.md` | Architecture + ADRs in `decisions/` |
| 05 | `05-implementation.md` | TDD log against the spec |

`STATUS.md` is the front-page tracker — current phase, last action, next action. `/wake` reads this when entering a project.

## Starting a new project

1. `cp -r _template/ <project-name>/`
2. Fill in `<project-name>/README.md` with a one-paragraph pitch.
3. Set `STATUS.md` to phase 01.
4. Walk forward through the phase files. Each one's prompt section explains what to produce and when the phase is done.

## Phase rules

- **The template is a maximum, not a minimum.** Skip phases that don't add value for a small project — leave a one-line note in the saved response saying why.
- **Don't skip backwards silently.** If you discover a requirement during design, update `02-requirements.md` and note the change in `STATUS.md`.
- **Each phase has a prompt and a saved response.** The prompt is durable (copied from `_template/`). The saved response is what the agent fills in.

## Public surface

`projects/` is collaborator-facing. Anything personal (names, machine specs, private context) belongs in `will-personal/` instead. Project artifacts here should be readable by someone who only sees this repo.
