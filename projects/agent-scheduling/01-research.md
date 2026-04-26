# 01 — Research

## Prompt

You are entering the research phase of this project.

**Goal:** Survey the problem space. Understand what already exists, what's been tried, where the constraints live. The output is a short, dense memo that lets a reader skip a week of digging.

**Activities:**
- Identify 3–5 prior solutions or analogous systems. For each: how it works, what it nails, where it falls short for our context.
- Note the hard constraints (legal, technical, social, economic) that bound any solution.
- Identify the open variables — things that genuinely require a choice during requirements/spec.
- Flag what we don't yet know and how to find out cheaply.

**Exit criteria:**
- A reader unfamiliar with this domain can finish the saved response and decide whether the project is worth pursuing.
- Constraints are concrete enough to be cited from `02-requirements.md`.

**Out of scope:**
- Choosing a solution (that's `04-design`).
- Writing requirements (that's `02-requirements`).

**When this phase makes sense to skip:** the problem space is well-understood by Chip already and the agent's research adds no new ground. In that case, write a one-sentence note in the saved response explaining the skip and listing the conditions that would re-open the phase.

---

## Saved response

*Skipped on initial draft (2026-04-22).* Chip wrote the proposed architecture directly from prior personal experience with cohort scheduling and from familiarity with the FastAPI / WebSocket / Anthropic-API stack. Treat this as a deliberate skip.

**Re-open this phase if any of:**
- We hit a hard wall in design and need to look at how comparable tools handle multi-party negotiation. Candidates to study: Doodle, When2meet, Calendly group polls, IETF iMIP/iTIP, Google Calendar's built-in "Find a time," Microsoft FindTime.
- A third-party library (commercial or OSS) would change the build/buy calculus.
- A new collaborator joins and pushes back on the architectural assumptions.
