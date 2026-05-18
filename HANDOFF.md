# will — Agent Handoff
*Last updated: 2026-05-10 (from session reflection)*

This is the system-level context loaded by `/wake` before any subject-repo briefing.
It re-establishes the thinking frame and durable cross-cutting facts of the whole ecosystem.

---

## Latest session thinking frame (2026-05-10)

This session executed **Phase A of the desktop-homelab project** end-to-end: drive survey → migration plan with Chip's decisions → Python script with dry-run → autonomous execute → recovery from in-flight bugs → 63.6 GB / 328,771 files staged cleanly on E:\\_migration\\. The autonomous-build pattern (pre-flight → walk steps → commit per logical unit → stop at boundary → STATUS writeup) transferred from agent-scheduling's TDD walks to a data-migration walk without modification. The "boundary" here is "physical hardware change required" (install USB, BIOS) just like agent-scheduling's "credentials required."

**Drive layout (post-Linux end state — was finalized this session):**

- **C:** NVMe 477GB → Linux root + `/home`, **ext4** (boot from here). Wipes current Windows during install.
- **D:** NVMe 477GB → `/workspace` (`_code`, `_notes`), **ext4** conversion last.
- **E:** HDD 2.8TB → `/srv/nas`, **NTFS kept** (Chip's explicit decision — don't reformat).
- **F:** SATA SSD 224GB → `/srv/media`, **ext4** (music + voice memos — SSD's no-spin-up-lag for streaming).

**Technical insights worth carrying forward:**

1. **`shutil.copytree` is brittle on real Windows trees.** Junction redirects, OneDrive cloud placeholders, access-denied subdirs, and file sources — any one kills the entire copytree call. Real-world solution: write your own walker with `os.walk` + per-file `try/except`. Reference impl: `projects/desktop-homelab/tools/drive_migration_stage.py::safe_copytree`. Skips Windows reparse points via `FILE_ATTRIBUTE_REPARSE_POINT` (0x400), handles file sources via `copy2`, idempotent on re-run via dest-exists-with-matching-size check.

2. **Idempotency via size-match is high-leverage.** Recovery re-run took 8 seconds instead of re-copying 60+ GB because already-copied files were detected and skipped. Small code, big payoff.

3. **Fnmatch-on-basenames is the convention for excludes.** Path-style patterns (`"AppData\\Local"`) silently never match against basenames. Use the basename (`"Local"`) instead. Cost this session: ~4 min wasted I/O + a debugging round.

**Anti-patterns to avoid:**

- **Don't trust `shutil.copytree` on real Windows trees.** Use the `safe_copytree` shape (per-file try/except, reparse-point skip, idempotent size-match).
- **Don't use path-style patterns in basename-fnmatch excludes.** Write the pattern that matches the basename of the directory to skip.
- **Don't write multi-section summaries without a self-consistency pass.** When a summary contains cross-referenced facts (drive layouts, mount points, install targets), all sections must agree. Shipped a self-contradicting summary this session; Chip caught it ("will the Linux OS files be on F at the end") — answer was C:, not F: as a stray line claimed.
- **Don't interpret "commit" as a natural stop point in autonomous mode.** Mid-session I committed the v2 plan + script and parked. Chip's "haha you got stuck" was the wake-up. A commit is a save-point, not a stop-point. Keep going through to the explicit stop boundary (physical hardware, credentials, decision required).
- **Don't defend a prior decision when Chip asks "is X the best choice?"** Re-examine with new context. His terse questions point at design issues; re-examination is signal of trust.
- **Don't write angle-bracket placeholders in markdown source.** GitHub renders `<name>` as an HTML tag and eats it. Use `(name)` or backtick-wrap.
- **Don't conflate Microsoft-services with Microsoft-protocol-authorship.** SMB/Samba is fine; the "no Microsoft" constraint is about managed services and lock-in.
- **Don't fill 03-specification or 04-design saved-response sections from conversation when the actual spec/design hasn't been done.** Phase 03/04/05 stay prompt-only until they're worked. Capture only what's known.
- **Don't try phase 4 (Google adapter) for agent-scheduling with mocked Google libraries** — half-work disguised as progress. Wait for real creds.

**Implicit contracts:**

- **Migration tools follow the dry-run-first pattern.** Editable Python plan file → script reads `PLAN` list → dry-run reports sizes + conflicts → human eyeballs → `--execute` touches disk. State file makes runs resumable. This is now a pattern, not a one-off.
- **For long-running scripts, use Monitor + run_in_background Bash pair.** `tail -f log | grep --line-buffered "completion|error"` for per-event notifications; background Bash for the definitive completion signal. No polling, no sleeping.
- **For homelab/infrastructure planning, the development approach is:** discuss → lock decisions → spawn project → write ADRs while reasoning is fresh → defer spec/design until physical work surfaces concrete facts. Template is a maximum, not a minimum.
- **When making infrastructure recommendations, present 2+ real options with honest tradeoffs.** "Let's go with all your recommendations" is the test that the framing was honest.
- **HANDOFF cleanup is integrated into the session, not deferred to /reflect.** When Chip closes carry-forward items in his first message, drop them from HANDOFF.md immediately.
- **"Build it" = autonomous walk** (TDD, migration, or otherwise). Pre-flight check first; proceed with no permission popups; commit per logical unit; stop at the explicit boundary; STATUS update on stop.

**Design philosophy:**

- `will/projects/` = collaborator-facing software work; one project per directory; 5-phase template; ADRs in `decisions/`.
- The template is a **maximum**, not a minimum. Non-linear walks are allowed (desktop-homelab is at phase 05 with Phase A done while phases 03/04 saved-responses stay prompt-only — that's correct).
- Phase files are **dual-purpose**: top half is the prompt (durable); bottom half is the saved response (agent-filled).
- ADR lifecycle: Proposed → Accepted (date-stamped); never edit Accepted Decision section, supersede with a new ADR instead.
- ADRs can be written immediately when infrastructure choices land via discussion. They're downstream of resolved requirements, not upstream.
- **safe_copytree design**: per-file try/except + accumulated skip-list, proactive reparse-point skipping, separate file-vs-tree handling, idempotent on re-run, returns `(files_copied, skipped_list)` instead of throwing on partial failure.

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

- [ ] Linux migration: dual-boot Ubuntu 24.04 on 240GB SATA SSD — actively wanted (2026-05-09); laptops are bought so the desktop is no longer blocked
- [ ] AI accelerator: AMD RX 7900 XTX decided as GPU baseline; Wormhole n150d for PCIE3 later. AMD employee discount no longer being tracked here — Chip handles purchase pricing himself.
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
- [x] **Merge money + health ingest flows.** DONE 2026-05-17 — `tools/ingest.py` + `tools/extract/` graduated to `will/tools/`. Single source of truth. No per-repo wrappers (rip-and-replace). Triggered earlier than the planned profile criterion: rule of 3 fired when `home` became the third consumer, and a real bug (money's older ingest.py missing YouTube support → garbage scraped output) cost time in the same session. Unified version adds clean_md call into the pipeline (the skill description had promised this but neither prior version delivered it). Consumer repos invoke via `uv run --project D:/_code/will python D:/_code/will/tools/ingest.py <source>`.
- [ ] **`desktop-homelab` project.** `projects/desktop-homelab/` created 2026-05-09 from template. Goal: convert the X299 desktop from Windows 10 to Ubuntu 24.04, expose existing storage as family-shared Samba NAS, host Navidrome music streaming for phone-via-BT-to-car, and run Claude Code as a long-running tmux session reachable over Tailscale from phone and laptop. Phases 01-research and 02-requirements completed in conversation; ADRs 0001–0004 written for distro / mesh / NAS / music decisions. **Next:** phase 03-specification — Samba share layout, Navidrome library structure, hostnames on the mesh, user-facing CLI surface. Open: NAS disk redundancy, headless vs. desktop boot, backup destination.
- [ ] **`email-connector` project (parked).** `projects/email-connector/` created 2026-04-27 from template. Goal: capability in `will` to read the user's email so newsletter/research mail can be auto-ingested. Code+skill+setup live in `will/`; credentials+mailbox URIs+OAuth tokens live in `will-personal/`. No driving deadline — start with phase 01-research when picked up. Likely strong overlap with the agent-scheduling Google OAuth slice (25–28) — both will need a Google client setup, so coordinate so credentials are obtained once.
- [ ] **Auto-improve principle for ingest tooling** is novel-ish and applies broadly (positions, papers, possibly emails when email-connector lands). Worth writing up as a system convention if a 3rd ingest type confirms the pattern. Reference impl: `clean_md.py` profiles dict (papers) + planned `ingest-positions` skill auto-improve checks (positions). (from money session 2026-04-27)
- [ ] **Status-flipping living-doc pattern** (sections move from `open` to `resolved YYYY-MM-DD` with stated rule, evidence accumulated pre-resolution) is generalizable. Reference impl: `money/research/investment-strategy.md`. If a 2nd domain adopts it (health strategy? writing process?), graduate to a system convention. (from money session 2026-04-27)
- [x] **Rename `health-ingest` plugin to `ingest`.** DONE 2026-05-17 — done at the same time as the ingest-tooling graduation (above), since both shipped together. Restart Claude Code to pick up the new plugin name. Future skills for ingest-positions / ingest-emails can join this plugin under `will/plugins/ingest/skills/`.
- [ ] **Auto-improve principle now demonstrated 3x** — papers (clean_md profiles in `ingest-paper`), positions (ingest_positions.py parser fix surfaced as auto-improve candidate), prices (CUSIP override candidates from `prices.py` first run). Per the 2026-04-27 HANDOFF item, write up `will/system/auto-improve.md` (or merge into a tooling-conventions doc). The pattern is: each tool run evaluates whether it needs updating and **surfaces candidates, not auto-applied changes**. (from money session 2026-04-28)
- [ ] **Pivot views via Excel Table with auto-filter** is a tooling pattern that may apply across repos. Reference impl planned at `money/tools/xlsx-export-plan.md`. If a 2nd repo wants the same (writing? health?), graduate the openpyxl Excel-Table helper to `will/tools/`. (from money session 2026-04-28)
- [ ] **The "no-pipe" rule for tool calls** is specific to projects using a `Bash(uv run python tools/:*)`-style allowlist (which is several repos by now). The matcher splits on `|` / `>` / `2>&1` — adding pipes to a tool invocation triggers a permission prompt every time. Worth a note in `will/system/` about how project allowlists interact with compound shells, so the convention propagates. (from money session 2026-04-28)
- [ ] **Project genesis modes are plural** — desktop-homelab proved the template handles **conversation-first** project creation as a 2nd successful genesis mode (after agent-scheduling's doc-migration-first). After a 3rd project uses the template (any mode), `/project` skill graduation per rule of 3 is justified. Strengthens the existing "5-phase template is diagnostically valuable" item. (from will session 2026-05-09)
- [ ] **ADRs-while-fresh pattern.** When infrastructure choices land via a discussion that already resolved requirements, write ADRs immediately rather than deferring to phase 04-design. Reference impl: desktop-homelab ADRs 0001–0004 (2026-05-09). The agent-scheduling rule "don't jump to architecture before requirements" still applies; this is downstream of resolved requirements, not a violation. Worth a note in the template's ADR README once a 3rd instance lands. (from will session 2026-05-09)
- [ ] **safe_copytree is a generic pattern.** Real Windows trees break `shutil.copytree` on reparse points (junctions, cloud placeholders), access-denied subdirs, and file sources. Per-file try/except + reparse-point skip + idempotent size-match is the right shape. Reference impl: `projects/desktop-homelab/tools/drive_migration_stage.py` 2026-05-10. After a 2nd use case (likely Phase B finalize script, or any future migration), graduate to `will/tools/safe_copy.py`. (from will session 2026-05-10)
- [ ] **Fnmatch-on-basenames is the exclude convention.** Path-style patterns (`"AppData\\Local"`) silently never match in the `matches()` helper used by the migration script. Write basename patterns. Worth a note in a tooling-conventions doc when one is written. Cost this session: ~4 min wasted I/O + a debugging round. (from will session 2026-05-10)
- [ ] **Multi-section summaries need a self-consistency pass.** When a single message contains cross-referenced facts (drive layouts, mount points, install targets), all sections must agree. Shipped a self-contradicting summary 2026-05-10 (drive layout said C:=Linux root, next-steps said install on F:); Chip caught it. Final-pass review is the fix. Could be tooled later (sanity check that drive-letter references in a doc agree on roles). (from will session 2026-05-10)
- [ ] **Autonomous-build pattern transfers from TDD to migrations.** Same shape: pre-flight → walk steps → commit per logical unit → stop at boundary → STATUS writeup. Phase A migration was the 2nd instance after agent-scheduling phases 1–3. After a 3rd domain uses it (content migration in money/health, etc.), generalize to `will/system/autonomous-build.md` as previously planned. (from will session 2026-05-10)
