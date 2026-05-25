# will — Agent Handoff
*Last updated: 2026-05-17 (from session reflection)*

This is the system-level context loaded by `/wake` before any subject-repo briefing.
It re-establishes the thinking frame and durable cross-cutting facts of the whole ecosystem.

---

## Latest session thinking frame (2026-05-17)

Two big things across four repos this session:

1. **Bootstrapped a new life-domain repo (`home`).** Chip moved into an Austin Hill Country property (~0.5 acre, mostly woods, pool, dog run, old garden plot to reclaim). `home` is the stewardship repo, parallel to `health`, `money`, `writing`, `vibedaw` — but **intentionally a single private repo with no `home-personal` split**, because home stewardship has no framework-vs-data distinction the way medical or financial work does.

2. **Graduated the ingest pipeline to `will/tools/`.** Three repos had diverged copies of `tools/ingest.py` + `tools/extract/`. The rule-of-3 trigger fired, *and* a real bug from divergence cost time mid-session (money's ingest.py lacked YouTube support; "successful" YT ingests scraped only the YouTube page footer). Unified version at `will/tools/ingest.py` now serves all three. Plugin renamed `health-ingest` → `ingest` at the same time. Standing HANDOFF items closed.

**The new ingest invocation pattern (durable):**

```
uv run --project D:/_code/will python D:/_code/will/tools/ingest.py <source>
```

Run from any subject repo's cwd → output to `<cwd>/research/refs/`. Caller's cwd determines destination; will's venv provides the deps.

**Plant-interests framing (preliminary — one batch of 10 sources):**

Themes consistent across the first batch:
- **Multi-purpose plants only** (food + wildlife + medicine + ornamental)
- **Indigenous/traditional knowledge as credibility filter** ("Egyptian grain farmers", "Medieval monasteries", "Indigenous tribes called")
- **Anti-chemical / pro-natural-systems**
- **Perennials and natives over annuals**
- **Wildlife-positive system thinking** (yard as ecology, not stage)
- **High-value specialty interest** (mpingo, tonewood)

Working framing for `home` agents:

> Chip's plant interests skew toward: multi-purpose perennials, native or well-adapted naturalized species, indigenous/traditional knowledge as a credibility filter, wildlife-positive systems, chemical-minimal approaches, and specialty/high-value species. Annual monocultures, chemical-input landscapes, and single-purpose ornamentals are out of scope.

**Don't lock it in yet.** Chip explicitly asked to discuss patterns "as they emerge" across multiple batches.

**Technical insights worth carrying forward:**

1. **Tool divergence across repos is a real failure mode.** Health had YouTube support, money had clean_md, neither had both. Bug surfaced only when home became the 3rd consumer. Rule-of-3 is the right graduation trigger.

2. **Skill description ≠ code reality.** `ingest-paper` SKILL.md promised clean_md integration; neither prior `ingest.py` actually called it. Unified version does. Anti-pattern worth memorializing.

3. **JS-walled HTML has a documented fallback.** Sites like thespruce.com block trafilatura AND WebFetch. Recipe: `curl -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15" "https://web.archive.org/web/2024/<original-url>" -o /tmp/<slug>.html` → ingest local. Should be added to `ingest-paper` SKILL.md as step 3f.

4. **Cwd-relative paths break shared scripts.** For will/tools/ scripts called from any subject repo: use `Path(__file__).parent / "<resource>"` for sibling resources; keep `Path("research/refs")` cwd-relative for output. Output stays caller-relative; resources stay script-relative.

5. **YouTube ingest requires explicit detection.** URLs containing `youtu.be/` or `youtube.com/` must invoke yt-dlp, not the html extractor. Otherwise: only the YouTube page footer is captured. Unified version handles this.

**Anti-patterns to avoid:**

- **Don't delete duplicates before testing the unified version.** Build-test-then-delete order. If test fails, working duplicates are still in place.
- **Don't claim "marginal" quality output for VTT as failed.** Auto-transcripts score lower because they lack punctuation. Unified version skips quality scoring for VTT.
- **Don't write SKILL.md prose that promises code behavior that doesn't exist.** Either implement first or mark explicitly as "planned, not yet implemented."
- **Don't auto-trust commit timestamps as "more recent = better."** Two diverged versions can each have features the other lacks. Read both before copying one.
- **Don't write home/HANDOFF.md or home/CLAUDE.md with aspirational content before the content exists.** Bootstrap skeletons, fill after first real session.
- **For new ingest sources, always `wc -w` and `head` the result before claiming success.** YouTube transcripts that "succeeded" with 22-line output were actually scraped YouTube page chrome, not transcripts.

**Implicit contracts established this session:**

- **Cross-repo shared tools live in `will/tools/`, with deps in `will/pyproject.toml`.** Caller invokes with `--project D:/_code/will`. Output is cwd-relative.
- **Plugin naming is repo-agnostic.** `health-ingest` → `ingest` because it serves health, money, and home. Future plugins serving multiple repos should be named for the function.
- **Home repo breaks the public-framework / private-data split** for stewardship-style life domains. Single private repo. Document the why in CLAUDE.md.
- **Plant research goes into `home/research/refs/` (flat structure)** — no topic subfolders until corpus warrants it.
- **For multi-repo refactors**: use TaskCreate to track sequencing, build-test-then-delete, commit each repo's diff with a focused message, run `uv sync` to prune lockfiles after pyproject changes.

**Design philosophy of the unified ingest pipeline:**

- One ingest.py at the meta-level, called from any subject repo's cwd
- Sources: file paths (PDF/DOCX/VTT/HTML), URLs, YouTube links
- YouTube auto-handled via yt-dlp (download VTT, extract, cleanup tmp)
- clean_md profile system runs between extract and quality (auto-detect by signature regex; profile name appears in YAML header)
- VTT skips cleanup and quality (transcripts are inherently raw/clean)
- Output: `<cwd>/research/refs/<slug>.md` with YAML frontmatter
- Skill (`ingest-paper`) lives in `will/plugins/ingest/` and instructs the agent on entry point + fallback chain

**Carry-forward design philosophy (still applicable from prior sessions):**

- `will/projects/` = collaborator-facing software work; one project per directory; 5-phase template; ADRs in `decisions/`.
- The template is a **maximum**, not a minimum. Non-linear walks allowed.
- Phase files are **dual-purpose**: top half prompt (durable); bottom half saved response (agent-filled).
- ADR lifecycle: Proposed → Accepted (date-stamped); never edit Accepted, supersede with new ADR.
- ADRs can be written immediately when infrastructure choices land via discussion. Downstream of resolved requirements, not upstream.
- **safe_copytree design** (from 2026-05-10): per-file try/except + accumulated skip-list, proactive reparse-point skipping, separate file-vs-tree handling, idempotent on re-run.
- **When making recommendations, present 2+ real options with honest tradeoffs.** "Let's go with all your recommendations" is the test that framing was honest.
- **Don't defend a prior decision when Chip asks "is X the best choice?"** Re-examine with new context.
- **Don't write angle-bracket placeholders in markdown source.** GitHub eats `<name>`. Use `(name)` or backtick-wrap.
- **Don't conflate Microsoft-services with Microsoft-protocol-authorship.** SMB/Samba fine; "no Microsoft" applies to managed services.

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
- [ ] **Skill-description-vs-code parity is a real anti-pattern.** Caught 2026-05-17 — `ingest-paper` SKILL.md described clean_md integration in detail (with sample stderr output, "extend, don't hand-edit" guidance) but neither `health/tools/ingest.py` nor `money/tools/ingest.py` actually called clean_md. The unified `will/tools/ingest.py` now does. Convention worth memorializing: when a SKILL.md describes code behavior, the code must exhibit it OR the description must say "planned, not yet implemented." If a 2nd instance lands, write `will/system/skill-code-parity.md`. (from will session 2026-05-17)
- [ ] **Archive.org-via-curl is a documented fallback for JS-walled HTML.** Pattern: `curl -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15" "https://web.archive.org/web/2024/<original-url>" -o /tmp/<slug>.html` → ingest local. Tested 2026-05-17 on thespruce.com — succeeded where trafilatura, WebFetch, and direct curl all failed. Worth adding to the `ingest-paper` SKILL.md fallback chain as step 3f. (from will session 2026-05-17)
- [ ] **Tool+skill pattern is now demonstrated 2x with full pair**: `commit-push` (tool + skill at `will/`) and `ingest` (tool + skill at `will/`, graduated this session). Plus `revert_ingest.py` as a tool-only candidate. After a 3rd full pair lands, write `will/system/tool-skill-pairs.md`. (consolidates earlier carry-forward; 2x as of 2026-05-17)
- [ ] **Project genesis modes — `home` is a 3rd mode**: bare-repo, no template. Life-domain repos (parallel to health/money/writing/vibedaw) don't follow `projects/_template/` — they're not software projects. Worth noting in the eventual `/project` skill spec that the template is for software projects only. (from will session 2026-05-17)
- [ ] **New life-domain repo: `home`** (ChipJust/home, private, single-repo no -personal split). Stewardship of Austin property: pest control (DE + FSL + Cedarcide), garden reclamation, planting research, permaculture. 15 sources ingested across batches 1+2. Plant-interests framework refined 2026-05-24 in `plans/plant-interests.md` (hard rules: no toxic, no chemical defaults, no managed-services deps; 8 criteria). Property mapping bootstrapped 2026-05-24 (TCAD polygon + USGS LIDAR fetch tool). Confirm/refine framing across further batches.
- [ ] **Skill-vs-tool popup pattern** — when an agent-level workflow requires pre-steps before a tool call, those pre-steps should move INSIDE the tool, not stay in the docs. Demonstrated 2x: (1) clean_md graduation into ingest.py (2026-05-17); (2) YouTube `yt-dlp --get-title` baked into ingest.py (2026-05-24, retired 6 popups/batch). After a 3rd instance, write `will/system/skill-tool-popup-pattern.md` alongside the tool-skill-pairs convention. (from home session 2026-05-24)
- [ ] **`data/` convention for large geospatial / binary data** — gitignore by file extension (`*.laz`, `*.las`, `*.tif`, `*.tiff` and `data/**/lidar/`, `data/**/derived/`), commit small structured data (boundaries .geojson, attribute tables) alongside. Reference impl: `home/data/property-map/` 2026-05-24. If a 2nd repo needs the same shape (money for binary OHLC caches? health for DICOM?), graduate to a system convention in `will/system/`. (from home session 2026-05-24)
- [ ] **Plugin rename → restart-required for skill-name visibility.** After a plugin rename, the session's skill registry shows OLD name even though `installed_plugins.json` and underlying machinery use the NEW name. Demonstrated 2026-05-24 with `health-ingest:ingest-paper` lingering a week post-rename. **Workaround:** call the underlying tool directly (`uv run --project D:/_code/will python D:/_code/will/tools/...`). Worth a one-liner in this HANDOFF (or a system note) so future agents don't get caught the same way. If it recurs, document. (from home session 2026-05-24)
