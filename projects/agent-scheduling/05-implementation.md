# 05 — Implementation

## Prompt

You are entering the implementation phase. Build the system using **test-driven development**.

**The TDD cycle (Kent Beck — red / green / refactor):**
1. Pick the smallest behavior from the spec that isn't yet implemented.
2. Write a failing test that asserts that behavior. Run it, watch it fail (red).
3. Write the minimum code that makes the test pass (green).
4. Refactor with tests green: extract, rename, dedupe.
5. Commit at green. Repeat.

**Activities:**
- For each phase from `04-design`, work through the TDD cycle until that phase's behaviors are covered.
- Maintain a running log in the saved response — one entry per cycle (test name, what it drove out, any surprise).
- Track deferred work explicitly: if you skip a behavior, record it under "Deferred" with reason and conditions for picking it back up.
- When you discover the spec or design is wrong, stop, fix the upstream document, then continue. Do not patch silently.

**Exit criteria:**
- Every spec behavior has at least one test.
- All tests are green on `main`.
- Deferred-work list is current and triaged.

**Out of scope:**
- Architectural rework (return to `04-design` and add an ADR).
- Net-new features beyond the spec (return to `02-requirements` first).

---

## Saved response

*Implementation has not started. Pre-conditions: spec finalized (03), at least ADRs 0001–0003 Accepted (04). Then begin TDD against phase 1 of the design's implementation phases.*

### TDD log

*(empty until phase begins)*

### Deferred

*(empty)*

### Operational notes

*(empty)*
