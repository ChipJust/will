# will — Agent Handoff
*Last updated: 2026-04-26 (from session reflection)*

This is the system-level context loaded by `/wake` before any subject-repo briefing.
It re-establishes the thinking frame and durable cross-cutting facts of the whole ecosystem.

---

## Latest session thinking frame (2026-04-26)

This session moved on three fronts that all served one direction: *make `will` a place where software actually gets built collaboratively, then exercise the new infrastructure on a real project end-to-end.*

1. **`will/projects/` is now the collaborator-facing surface for software work.** The will/will-personal split is by **audience**, not by category — collaborator-facing artifacts (plans, designs, problems-as-design-proposals) live in `will/`; personal/ops issues live in `will-personal/problems/`. The 5-phase template (research → requirements → spec → design → implementation TDD) at `will/projects/_template/` is the canonical way to start a project. Each phase file is dual-purpose: durable prompt at top, agent-filled saved response at bottom. ADRs in a `decisions/` subfolder use Nygard format.

2. **The template proved itself diagnostically.** Migrating `agent-scheduling.md` (a 2026-04-22 architecture note) into the template surfaced that the original doc had skipped requirements and gone straight to architecture. That's exactly the failure mode the template catches. STATUS dropped to phase 02 by virtue of the structure, and Chip then resolved every open requirements question in one round of Q&A — at which point spec/design rewrites were mechanical and ADRs 0001–0007 all moved to Accepted.

3. **The first end-to-end autonomous TDD build for the project landed.** After Chip said "build it," the agent walked slices 1–24 (out of 37) hands-off in one session: 135 tests, one commit per slice, ~24 commits in sequence. Phase 1 (skeleton + adapters + context), phase 2 (negotiator + batch CSP solver + deadlock + state persistence), and phase 3 (FastAPI chat server with WebSocket + SQLite) all done. Stopped cleanly at slice 25 (Google OAuth) because external credentials are needed. **Prototype target: Jun 1, 2026.**

**Anti-patterns to avoid:**

- **Don't write angle-bracket placeholders in markdown source.** GitHub renders `<name>` as an HTML tag and eats it. Use `(name)` or backtick-wrap. Don't ship `&lt;name&gt;` HTML entities — those just appear as literal text.
- **Don't write a "deadlock" / "infeasible" / "edge-case" test without first confirming the precondition holds.** Run the function-under-test and verify it returns the expected None/empty/etc. before asserting the consequence. Slice 17 surfaced this.
- **Don't put stub tests for "future slices add this" using a message type that's about to be implemented.** Pick a stub that won't be touched soon, or delete the stub when the future arrives.
- **Don't refactor existing slices "while I'm here" during a TDD walk.** Each slice is its own TDD cycle. Speculative cleanup violates YAGNI and creates noisy diffs.
- **Don't try phase 4 (Google adapter) with mocked Google libraries** — half-work disguised as progress. Wait for real creds.

**Implicit contracts:**

- **"Build it" = autonomous TDD walk.** Pre-flight check first; then proceed with no permission popups; commit per slice with descriptive subject; stop at credential boundary; write a STATUS update on stop.
- **One commit per slice.** No batching unless slices are deeply coupled. Granular history.
- **Heavy parallel doc writes after a decision lands.** Once requirements are resolved, the rewrites are mechanical — fire them in batches, not sequentially.
- **Pre-flight scaffolding before autonomous work.** Explicit "what I'd ask for if you have it now" + "where I'll stop without further input" + "my commitments while running."

**Design philosophy:**

- `will/projects/` = collaborator-facing software work; one project per directory; 5-phase template; ADRs in `decisions/`.
- The template is a **maximum**, not a minimum. Small projects skip phases.
- Phase files are **dual-purpose**: top half is the prompt (durable, copied from template); bottom half is the saved response (agent-filled).
- ADR lifecycle: Proposed → Accepted (date-stamped); never edit Accepted Decision section, supersede with a new ADR instead.

---

## Cross-cutting concerns (durable — read before working in any repo)

**Python:** 3.14.3 (uv-managed). `python` and `python3` both resolve to it via `~/.bashrc`. To upgrade: `uv python install 3.X` + update one line in `~/.bashrc`.

**Windows/Linux:** Currently on Windows 10 Pro. Linux migration is the recommended path for AI hardware support (AMD ROCm, Tenstorrent). See `will-personal/system/hardware.md` and `will-personal/hardware/projects/2026-hardware-refresh.md`. All tools are written to be portable — UTF-8 stdout wrappers, forward-slash paths in bash.

**AMD:** Chip works for AMD. Always prefer AMD CPU/GPU in hardware recommendations. No Intel CPU options unless explicitly requested.

**Encoding:** Any Python script that writes text must wrap stdout in UTF-8 and open files with `newline=""` for markdown/text output. Windows cp1252 silently corrupts special characters. `.gitattributes` (`* text=auto eol=lf`) is deployed to every repo to enforce LF in storage.

**Commit style:** "commit" = stage specific files + commit + push. No prompts. Never `git add -A`. Never commit PDFs, `.venv/`, `egg-info/`, or `output/`. Use `will/tools/commit_push.py` (pre-approved at user-global) instead of chaining `git add → commit → push`. The tool refuses secrets, directories, detached HEAD, and empty diffs.

**Edit/Write popups:** `permissions.defaultMode: "acceptEdits"` is set in user-global `~/.claude/settings.json`. Edits and writes don't prompt; review happens at commit time.

**Tool naming:** Every repo uses `tools/` for executable code. No more `agent-tools/`.

**Plugin install:** After adding or modifying a plugin in `will/plugins/`, run `bash plugins/install.sh` from the will repo root, then restart Claude Code.

**Permission patterns at user-global** (covers most agent operations without popups):
`Bash(uv run:*)`, `Bash(uv sync:*)`, `Bash(uv add:*)`, `Bash(uv lock:*)`, `Bash(uv python:*)`, `Bash(uvx:*)`, plus the standard read-only and git operations. See `~/.claude/settings.json`.

**Hardware tracking:** Machine records and purchase history live in `will-personal/hardware/machines/` (one file per machine). Project files in `will-personal/hardware/projects/`. Serial numbers and invoices go there, not in `will`.

---

## Session practices

- **Start:** `/wake` — loads this file + subject-repo HANDOFF.md, briefs on next steps
- **End:** `/reflect` — writes reflection to will-personal, updates subject-repo HANDOFF.md
- **Mid-session:** `/reflect review` — updates next steps list without full reflection

---

## Open system-level items

- [ ] Linux migration: dual-boot Ubuntu 24.04 on 240GB SATA SSD — linked to laptop purchase (see will-personal/hardware/projects/2026-hardware-refresh.md)
- [ ] AI accelerator: AMD RX 7900 XTX decided as GPU baseline; Wormhole n150d for PCIE3 later — pending Chip's AMD employee GPU discount check (see hardware project)
- [ ] Laptop purchase: 2× Lenovo Yoga 7a 2-in-1 Gen 11 — pending AMD Lenovo Affinity Store check (lenovo.com/us/vipmembers/amd/)
- [ ] Bootstrap: test setup.sh end-to-end on a clean Linux machine
- [ ] `giving`, `prayer`, `social-influence` repos: create when ready to start
- [ ] `writing` and `vibedaw` don't have HANDOFF.md files yet — will be created on first `/reflect` in those repos. `money` and `health` already follow the modern pattern. (Reframed 2026-04-25 from earlier "modernize" item.)
- [ ] Concept-skill pattern is likely cross-cutting. If money v2+ proves it out, the skill format + runtime should graduate to `will/plugins/` so health, writing, and others can adopt. (from money session 2026-04-20)
- [ ] Skill-as-knowledge-forwarding is a novel-ish pattern. Worth writing up as a system convention if concept-skills prove out — gives other repos a template for encapsulating and transferring domain knowledge rather than dumping raw docs (from money session 2026-04-20)
- [ ] Cleanup: `will/agent-tools/test.json` (junk session-log dump) and the now-empty `will/agent-tools/` directory after the rename to `tools/`. Needs Chip's confirm before `rm -rf`. (from will session 2026-04-25)
- [ ] Tool+skill pattern is now demonstrated by `commit_push.py` (full pair: tool + skill plugin) and `revert_ingest.py` (tool only, no skill yet). After a 3rd instance, write `will/system/tool-skill-pairs.md` documenting the lifecycle. (from will session 2026-04-25)
- [ ] Wrap `money/tools/revert_ingest.py` with a skill plugin so the agent discovers it via skill description, not just CLI knowledge. (from will session 2026-04-25)
- [ ] `agent-scheduling` project: phases 1–3 implemented (slices 1–24, 135 tests green) on 2026-04-26 in the autonomous build session. Phase 4 (Google OAuth + GoogleAdapter, slices 25–28) awaits Chip-supplied Google API client credentials and a test account. **Prototype target Jun 1, 2026.** (from will session 2026-04-26)
- [ ] Provision frontend tooling for agent-scheduling phase 5 (PWA, slices 29–33). Decide framework (React, SolidJS, plain Web Components, htmx) and seed the structure when ready. (from will session 2026-04-26)
- [ ] Decide if/when `agent-scheduling` graduates from `projects/` to its own repo (provisional name `convene`). Triggers: ships to first real users, OR the `will`-as-meta-agent vs `will`-as-multi-user-platform conflation creates friction. (from will session 2026-04-26)
- [ ] **Autonomous-build pattern is novel.** Pre-flight → walk slices → commit per slice → stop at credential boundary → STATUS update. Worth documenting at `will/system/autonomous-build.md` once a 2nd project uses it. Reference impl: agent-scheduling phase 1–3 build (2026-04-26). (from will session 2026-04-26)
- [ ] **The 5-phase project template is diagnostically valuable** — it surfaced that agent-scheduling's original doc had skipped requirements. After 1–2 more projects use it, evaluate the `/project` skill graduation per rule of 3. (from will session 2026-04-26)
- [ ] **Merge money + health ingest flows.** Both repos duplicate `tools/ingest.py` + `tools/extract/`. Skill (`ingest-paper`) is already cross-repo via plugin. Trigger: 2nd repo needs a cleaner profile that already exists in money (e.g. health gets a Gmail-print PDF). Action then: graduate `tools/extract/clean_md.py` (profiles dict) + `tools/extract/from_*.py` + `tools/ingest.py` to `will/tools/`, leave thin per-repo wrappers if needed. Single source of truth for profiles. (from will session 2026-04-26 — clean_md.py introduced for Bravos Gmail-print PDF.)
- [ ] **`email-connector` project (parked).** `projects/email-connector/` created 2026-04-27 from template. Goal: capability in `will` to read the user's email so newsletter/research mail can be auto-ingested. Code+skill+setup live in `will/`; credentials+mailbox URIs+OAuth tokens live in `will-personal/`. No driving deadline — start with phase 01-research when picked up. Likely strong overlap with the agent-scheduling Google OAuth slice (25–28) — both will need a Google client setup, so coordinate so credentials are obtained once.
