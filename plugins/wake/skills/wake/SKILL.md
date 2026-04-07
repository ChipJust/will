---
name: wake
description: Session start skill. Use when the user says "wake", "wake up", "pick up where we left off", "/wake", or opens a session and wants to re-establish context. Loads a four-layer context stack and presents a concise brief, then waits for direction.
argument-hint: [repo-name]
version: 1.2.0
---

# Skill: /wake — Session Start Review

Run this at the start of any session to re-establish context and agree on what to work on.

Context loads in four layers, from broadest to narrowest:

| Layer | File | What it contains |
|-------|------|-----------------|
| 1 | `will/HANDOFF.md` | System architecture, conventions, repo ecosystem |
| 2 | `will-personal/HANDOFF.md` | Who Chip is, values, cross-cutting personal items |
| 3 | `<repo>/HANDOFF.md` | Repo design, thinking frame, next steps |
| 4 | `<repo>-personal/HANDOFF.md` | Personal data layer for this repo (if exists) |

Layers 1–2 always load. Layers 3–4 load for subject repos (skip if working in `will` itself).
Layer 4 is optional — skip silently if the personal repo doesn't exist yet.

---

## Step 1 — Identify the repo

Determine which repo we're working in:
- If a repo name was passed as an argument, use that
- Otherwise detect from the current working directory

---

## Step 2 — Load all context layers

Read in order:

**Layer 1 — System** (`D:\_code\will\HANDOFF.md`):
- Architecture overview, repo ecosystem state
- Cross-cutting conventions (Python version, encoding, commit style)
- Open system-level items

**Layer 2 — Personal** (`D:\_code\will-personal\HANDOFF.md`):
- Who Chip is and how he collaborates
- Mission framing that applies across all repos
- Personal cross-cutting open items

**Layer 3 — Repo** (`D:\_code\<repo>\HANDOFF.md`):
- Thinking frame from the last session in this repo
- Open next steps: "Agent can start immediately" and "Needs Chip"
- Skip if working in `will` itself

**Layer 4 — Personal repo** (`D:\_code\<repo>-personal\HANDOFF.md`):
- Personal data and context specific to this repo (e.g. Chip's actual health records)
- Skip silently if `<repo>-personal` doesn't exist yet

If any expected HANDOFF.md is missing (Layers 1–3), note it — this means `/reflect`
was never run here. Fall back to the most recent reflection from `will-personal/reflections/`:
```
ls D:\_code\will-personal\reflections\ | grep <repo> | sort | tail -1
```

---

## Step 3 — Present the briefing

Output a concise two-section brief:

```
## Session Brief — <Repo> — <Date>

### System + Personal
<3–5 bullets maximum — only what's directly relevant to this session>
<Include any personal open items that touch this repo>

### This repo
**Thinking frame:** <1–2 sentences — the mental model to carry into this session>

**Open next steps:**

Agent can start immediately:
- [ ] <item>

Needs Chip:
- [ ] <item>

**Suggested starting point:**
<One sentence: highest-value item the agent can do without blocking on Chip>
```

Keep it short. System + Personal should be 3–5 lines, not a recap of every layer.
Surface only what's relevant to the work at hand.

---

## Step 4 — Triage with Chip

After presenting the brief, ask:

> "Want to start there, or is there something else on your mind for this session?"

Then wait. Do not propose a plan or start work until direction is confirmed.

Once confirmed:
- Working through the list: start on the first item
- New direction: note existing next steps are on hold, focus on the new thing

---

## Step 5 — Update HANDOFF.md after triage (optional)

If Chip closes out items during triage ("that's done", "drop that one"),
update the subject repo's HANDOFF.md before starting work:
```
cd D:\_code\<repo> && git add HANDOFF.md && git commit -m "Update handoff: triage YYYY-MM-DD" && git push
```

---

## Notes

- Fast — under a minute
- Layer 4 is the future home of personal medical records, personal financial data, etc.
  It doesn't exist for most repos yet — that's expected
- For mid-session next-steps review: `/reflect review`
- If HANDOFF.md is stale or missing anywhere, flag it and suggest `/reflect` at session end
