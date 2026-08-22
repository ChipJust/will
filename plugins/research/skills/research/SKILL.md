---
name: research
description: This skill should be used when the user asks for research, a "research round", "deep research", "look into X", "investigate X", or when the agent is about to launch research subagents or web searches for a substantive question. Enforces corpus-first lookup (avoid duplicate pulls), disciplined agent orchestration (no runaway child-spawning), and mandatory harvesting of every report into the repo's research library with index rebuild.
---

# Skill: research

Run research so that (1) nothing already in the corpus gets re-fetched, (2) agents
don't spawn runaway children, and (3) every report is persisted to markdown, indexed,
and committed — never lost in conversation context.

Tools (both in `will/tools/`, docstrings have full I/O samples):
- `research_index.py` — search/index the cross-repo corpus (`research/refs/` +
  `research/agent-reports/` in every repo)
- `harvest_agent_report.py` — extract a completed agent's final report from its
  transcript into `<repo>/research/agent-reports/` with frontmatter

## Step 1 — Corpus first, always

Before ANY web search or research agent launch:

```
uv run python D:/_code/will/tools/research_index.py --search "<topic keywords>"
```

For specific sources (a paper, a video, a URL the user gave):

```
uv run python D:/_code/will/tools/research_index.py --has-url "<url>"
```

- Hits → Read those documents first. Only research the *gaps*.
- No hits → the tool says web research is justified. Proceed.
- Note what the corpus already covers in the agent prompt so the agent doesn't
  redo it ("Our corpus already covers X and Y — do not research those").

## Step 2 — Launch discipline

When commissioning research agents:

1. **One agent per genuinely independent question.** If two questions share sources
   (e.g., "fluoride in water" and "pineal fluoride"), give them to ONE agent.
2. **Every agent prompt must include this block, verbatim:**

   > Before fetching any source, check the local corpus:
   > `uv run python D:/_code/will/tools/research_index.py --search "<terms>"`
   > and `--has-url "<url>"` for specific sources. Read local hits instead of
   > re-fetching. **Do not spawn more than 2 child agents, and prefer zero** —
   > do the searching yourself. If you spawn children, do not wait indefinitely:
   > if a child stalls, write your report with what you have and mark the gap.
   > Your final message must be the complete structured report (markdown,
   > sources cited with URLs, evidence-graded) — not a status update.

3. **Cap the fleet.** Default max 4 concurrent research agents. More requires the
   user's explicit spend approval (they are paying per token).
4. While agents run, audit cheaply if needed: transcripts live under
   `%LOCALAPPDATA%/Temp/claude/<project>/<session>/tasks/*.output`; use
   `harvest_agent_report.py --list` to see who is DONE vs RUNNING.
5. If an agent stalls waiting on its own children, send it a wrap-up directive via
   SendMessage rather than letting it idle.

## Step 3 — Harvest every report (mandatory)

When an agent completes, its report exists ONLY in conversation context and its
transcript — both ephemeral. Immediately:

```
uv run python D:/_code/will/tools/harvest_agent_report.py --agent <id> \
    --repo <repo> --slug <kebab-slug> --title "<Title>" \
    --question "<the question it answered>" \
    --findings "<one-line answer>" \
    --topics <comma,separated,keywords>
```

- `--repo` is the subject repo (health, home, money…), NOT will.
- Verify the word count printed is plausibly the full report (thousands of words,
  not tens). A tiny count means the agent's last text was a status line — the
  report may not exist yet, or arrived via the task notification instead; in that
  case write the notification text to the same path by hand (Write tool), same
  frontmatter.
- Personal-data boundary still applies: if the report contains the user's clinical
  or financial specifics, harvest to the `-personal` repo instead.

## Step 4 — Reindex and commit

```
uv run python D:/_code/will/tools/research_index.py
```

Then commit the new reports + regenerated `will/research-index.md` via commit_push
(separate calls per repo). The index is the artifact future sessions and agents
search — an unindexed report is invisible.

## Failure modes this skill exists to prevent

- **Duplicate pulls**: agent re-fetches a source already in `research/refs/` (267
  WebFetch domain approvals accumulated this way; agents re-researched fluoride
  three times in one session, 2026-08-22).
- **Research evaporation**: a 7,000-word cited report summarized to 10 lines in a
  synthesis doc, full text lost at session end.
- **Agent parties**: research agents spawning 5–7 children each, grandchildren
  spawning their own; 23 descendants from 5 parents (2026-08-22). The prompt block
  in Step 2 is the guard.
- **Straggler deadlock**: a parent idling 18+ minutes waiting for one lost child
  instead of shipping its report.
