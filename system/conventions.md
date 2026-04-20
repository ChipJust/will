# System-Wide Conventions

Rules that apply across all repos and all sessions. Claude reads these to
calibrate behavior without needing reminders.

**See also:** `context-architecture.md` for the linked-node pattern that
organizes knowledge across every repo. Any file you create should fit that
pattern (one topic per node, discoverable via an index, connected by explicit
links).

---

## Working style

**Bias toward action, not notes**
Before surfacing an observation to Chip, check: can I just do this?
Try 5-6 alternative approaches before deciding something requires his input.
Reserve notes for things that genuinely cannot be resolved without a decision from him.

**Commit means: stage + commit + push, no prompts**
"Commit" means stage all agent-modified files across all touched repos,
commit with a descriptive message, and push. No asking for confirmation.

**No unsolicited disclaimers**
Treat Chip as an informed adult. No safety warnings unless specifically relevant
and non-obvious. No "consult a professional" boilerplate.

---

## Code conventions

| Convention | Rule |
|------------|------|
| Branch | Always `main`, never `master` |
| Package manager | `uv` only — never `pip`, `pipx`, or `conda` |
| PDF generation | `tools/convert.py` (pypandoc/xelatex) |
| Research ingest | `tools/ingest.py` → `research/refs/` |
| Output dirs | gitignored (`output/`, `.venv/`, `__pycache__/`, `*.egg-info/`) |
| Encoding | Always UTF-8; wrap stdout with `io.TextIOWrapper` in scripts |

---

## Session conventions

**Run `/reflect` at the end of every session**
Write a dated reflection to `will/reflections/YYYY-MM-DD-<repo>.md`.
Commit it to the will repo.

**Memory is updated during sessions**
If something is learned about preferences, project state, or tooling,
update the relevant memory file immediately — don't defer to end of session.

---

## Repo conventions

Each repo is an agent. Each agent has:
- `CLAUDE.md` — tailored instructions for that context
- `research/refs/` — ingested external references (if applicable)
- `tools/ingest.py` + `tools/extract/` — ingest tooling (copied per repo)
- `.gitignore` — excludes `.venv/`, `output/`, `*.egg-info/`, `*.pdf` (source files)

Source PDFs stay local (gitignored). Only the ingested markdown is tracked.

---

## Citing sources

- Always cite sources; flag synthesis separately from sourced claims
- Prefer full-text ingestion over abstract-only; upgrade refs when PDFs become available
- Header format for ingested refs: YAML frontmatter with title, source_file/url,
  ingest_date, ingest_method, quality_score
