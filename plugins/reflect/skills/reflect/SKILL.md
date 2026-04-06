---
name: reflect
description: End-of-session reflection skill. Use when the user says "reflect", "end of session", "wrap up", "/reflect", or asks to write a session summary or reflection note. Writes a dated reflection file to the will repo and updates memory.
argument-hint: [repo-name]
version: 1.0.0
---

# Skill: /reflect — End-of-Session Reflection

Write a session reflection to `D:\_code\will\reflections\` and update memory.
Run this at the end of every working session in any repo.

---

## Step 1 — Determine context

- What repo were we working in? (default: detect from current working directory)
- What date is it? (use today's date from context)
- Output file: `D:\_code\will\reflections\YYYY-MM-DD-<repo>.md`
  - If a file for today's date and repo already exists, append a `-2` suffix

---

## Step 2 — Write the reflection file

Use this structure:

```markdown
# Session Reflection — <Repo Name>
**Date:** YYYY-MM-DD
**Repo:** `<repo>` (ChipJust/<repo>)

## What Was Built / Decided
<Bullet list of concrete outputs: files created, features added, decisions made>

## What Worked Well
<What to repeat in future sessions>

## What Could Be Improved
<Friction points, wrong assumptions, things that slowed us down>

## Decisions Made
<Non-obvious choices that future sessions should know about, with brief rationale>

## Things to Follow Up
- [ ] <Unfinished items or questions that surfaced>

## System Observations
<Anything about how the Claude Code system itself (skills, memory, hooks, tooling)
 could be improved based on this session>

## Handoff to Next Agent
<This is the most important section. Write it directly to the next Claude agent
that will work in this repo. Capture:
- The thinking frame that made this session productive — not just what was built
  but how to *think* about this space
- What the user responds well to (specific framing, level of detail, initiative)
- Anti-patterns to avoid (e.g. "don't propose to rebuild X — it already exists")
- The design philosophy of key systems, in a sentence each
- Any implicit contract established this session that isn't written elsewhere

This section should let the next agent pick up mid-thought, not start over.>

## Next Steps
<Re-read the Handoff section above, then scan the full session context for anything
actionable that wasn't already captured. Split into two groups:

**Agent can do immediately:**
- [ ] <Tasks the next agent can start without asking — code, file creation, grepping for gaps, etc.>

**Needs Chip:**
- [ ] <Items that require a decision, credential, or confirmation from Chip>

**Structural notes:**
- <Observations about the system itself — stale files, missing ORIENTATION.md, superseded reflections, etc.>

Be specific. Vague items belong in Things to Follow Up. This section is the startup checklist for the next session.>
```

Be specific and honest. Future sessions will read this to re-establish context.
Avoid generic statements like "the session went well."
The Handoff section is the most important for continuity; Next Steps is the immediate action list.

---

## Step 3 — Update memory

After writing the reflection, review whether any memory files need updating:

- Did you learn something new about how Chip prefers to work? → `feedback_*.md`
- Did the project state change significantly? → `project_*.md`
- Did you discover a new tool, convention, or preference? → appropriate memory type

Update or create memory files as needed. Do not duplicate what's already in memory.

---

## Step 4 — Update PLAN.md in will repo

If the session revealed a gap in the system architecture, a new repo is needed, or a
problem was logged or resolved, update `D:\_code\will\PLAN.md` accordingly:
- Add to revision history table
- Update repo status if applicable
- Add or close items in the open problems section

---

## Step 5 — Commit the reflection

```
cd D:\_code\will && git add reflections/ problems/ PLAN.md && git commit -m "Add session reflection: YYYY-MM-DD <repo>"
```

Then push: `git push`

---

## Notes

- The will repo lives at `D:\_code\will` (Windows) — adjust path if on a different OS
- If the will repo isn't cloned on this machine, flag it and write the reflection
  to a temp location, noting where it should go
- Reflections accumulate into an institutional memory of how the system was built
  and why — treat them as first-class artifacts
