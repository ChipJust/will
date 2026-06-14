# will — Agent Handoff
*Last updated: 2026-06-13 (from will session — housekeeping sweep)*

This is the system-level context loaded by `/wake` before any subject-repo briefing.
It re-establishes the thinking frame and durable cross-cutting facts of the whole ecosystem.

---

## Latest session thinking frame (2026-06-13)

Housekeeping sweep — graduated three conventions that had hit rule-of-3, fixed a
real ingest bug, and cleaned up stale HANDOFF items accumulated since 2026-05-17.

**What shipped this session:**

1. **Wrote `system/skill-tool-popup-pattern.md`** — 3rd instance (PDF URL detection)
   landed 2026-05-31; now documented. The pattern: deterministic pre-steps in skill
   docs should move inside the tool to eliminate permission popups.

2. **Wrote `system/auto-improve.md`** — 3 instances (clean_md profiles, position parser,
   CUSIP overrides) documented. The pattern: tools surface improvement candidates on
   stderr, never auto-apply.

3. **Fixed ingest.py PDF-URL detection.** URLs ending in `.pdf` now auto-download to a
   temp file and route to pymupdf instead of failing through the HTML extractor.

4. **Updated `system/conventions.md`** — corrected stale ingest-tooling note (was "copied
   per repo", now reflects the graduated single-source-of-truth at `will/tools/`).

5. **Cleaned up stale HANDOFF items** — `agent-tools/` directory already gone (marked done),
   consolidated duplicate items, noted agent-scheduling Jun 1 deadline has passed.

**Prior session context (2026-05-17 through 2026-05-31):**

Bootstrapped `home` repo, graduated ingest pipeline to `will/tools/`, ran home-domain
research batches (15 sources across plants/permaculture/pest-control/snake-ecology),
built property-mapping tools (TCAD polygon + USGS LIDAR), refined plant-interests
framework. See items below for carry-forward details.

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

## Cross-repo survey (2026-06-13)

Surveyed all ecosystem repos. HANDOFFs updated where stale (home, health).
Sorted by staleness — oldest first.

### health (HANDOFF: 2026-04-11 — 63 days stale)

Agent can start:
- [ ] Analyze `research/refs/this-tiny-molecule-blocks-aging.md` — summarize claims, assess evidence, implications for Chip's stack
- [ ] Grep `research/refs/` for abstract-only entries missing `source_url`; add DOIs
- [ ] HANDOFF refresh — updated ingest note (now references will/tools/) but framing is stale
- [ ] Investigate untracked `medical-history/` dir and `transcript.en.vtt` in working tree

Needs Chip:
- [ ] Source URLs for abstract-only refs where DOI isn't findable
- [ ] Paige's BP medication name + class, allergy details (blocks health-personal stack draft)
- [ ] Any new labs or records for Chip

### money (HANDOFF: 2026-04-28 — 46 days stale)

Agent can start:
- [ ] Build `--xlsx` flag for `current_positions.py` (spec at `tools/xlsx-export-plan.md`)
- [ ] HANDOFF refresh — 46 days stale, rebalance state likely outdated
- [ ] Investigate untracked `data/current-positions.md` in working tree

Needs Chip:
- [ ] Rebalance status check — $128K gap was due 2026-05-08 (36 days past); KGC + ORLA dispositions
- [ ] ELE mistake position — sell-back timing
- [ ] Social-impact filter — was deferred to after 2026-05-08, now overdue
- [ ] CUSIP override candidates → build `data/cusip-overrides.csv`?

### home (HANDOFF: 2026-06-13 — reflected this session)

Agent can start:
- [x] ~~derive_terrain.py~~ — DONE. laspy + scipy + numpy. DEM + DSM + hillshade + slope + aspect.
- [x] ~~solar_exposure.py~~ — DONE. pvlib Ineichen clear-sky. 583–2479 kWh/m²/yr.
- [x] ~~terrain_viewer.py~~ — DONE. Rewritten from plotly to three.js. NAIP satellite drape. 0.5 MB.
- [x] ~~research/refs/ subfolder reorg~~ — DONE. plants/ (16), snakes/ (10), birds/ (5), design/ (2).
- [ ] **Phase A — Manual scene bootstrapping** (plans/3d-model.md). Create scene.json, render envelopes.
- [ ] Slope/drainage/sun-exposure interpretation from terrain data

Needs Chip:
- [ ] Property walk with phone (40-60 photos/tree for COLMAP capture pipeline)
- [ ] Site walk, garden assessment, inventory walk, Texas811 call
- [ ] Pest-control products, cultivar selections, hugelkultur trench location

### writing (no HANDOFF — never `/reflect`ed)

- [ ] Needs first `/reflect` session to create HANDOFF.md
- No active work items visible; last commit was writing-preferences refinement

### vibedaw (no HANDOFF — never `/reflect`ed)

- [ ] Needs first `/reflect` session to create HANDOFF.md
- [ ] Untracked `.mcp.json` in working tree — gitignore or commit?
- Extensive design docs but no implementation started; pyproject.toml + deps not yet set up

### Projects in will

**agent-scheduling:** Phase 4 blocked on Google OAuth credentials + test account. Jun 1 prototype target past due — re-scope or supply credentials.
**desktop-homelab:** Phase A complete (63.6GB staged on E:\). Phase B blocked on physical Linux install (Ubuntu 24.04 on C: NVMe).
**email-connector:** Parked. No driving deadline. Likely shares Google OAuth work with agent-scheduling.

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
- [x] Cleanup: `will/agent-tools/` directory — already removed as of 2026-06-13 check (was empty after rename to `tools/`). (from will session 2026-04-25, closed 2026-06-13)
- [x] Tool+skill pattern item — superseded by consolidated item below (2x full pairs as of 2026-05-17). (from will session 2026-04-25, consolidated 2026-06-13)
- [ ] Wrap `money/tools/revert_ingest.py` with a skill plugin so the agent discovers it via skill description, not just CLI knowledge. (from will session 2026-04-25)
- [ ] `agent-scheduling` project: phases 1–3 implemented (slices 1–24, 135 tests green) on 2026-04-26 in the autonomous build session. Phase 4 (Google OAuth + GoogleAdapter, slices 25–28) awaits Chip-supplied Google API client credentials and a test account. **Prototype target was Jun 1, 2026 — past due; needs Chip to re-scope or supply credentials.** (from will session 2026-04-26, updated 2026-06-13)
- [ ] Provision frontend tooling for agent-scheduling phase 5 (PWA, slices 29–33). Decide framework (React, SolidJS, plain Web Components, htmx) and seed the structure when ready. (from will session 2026-04-26)
- [ ] Decide if/when `agent-scheduling` graduates from `projects/` to its own repo (provisional name `convene`). Triggers: ships to first real users, OR the `will`-as-meta-agent vs `will`-as-multi-user-platform conflation creates friction. (from will session 2026-04-26)
- [ ] **Autonomous-build pattern is novel.** Pre-flight → walk slices → commit per slice → stop at credential boundary → STATUS update. Worth documenting at `will/system/autonomous-build.md` once a 2nd project uses it. Reference impl: agent-scheduling phase 1–3 build (2026-04-26). (from will session 2026-04-26)
- [ ] **The 5-phase project template is diagnostically valuable** — it surfaced that agent-scheduling's original doc had skipped requirements. After 1–2 more projects use it, evaluate the `/project` skill graduation per rule of 3. (from will session 2026-04-26)
- [x] **Merge money + health ingest flows.** DONE 2026-05-17 — `tools/ingest.py` + `tools/extract/` graduated to `will/tools/`. Single source of truth. No per-repo wrappers (rip-and-replace). Triggered earlier than the planned profile criterion: rule of 3 fired when `home` became the third consumer, and a real bug (money's older ingest.py missing YouTube support → garbage scraped output) cost time in the same session. Unified version adds clean_md call into the pipeline (the skill description had promised this but neither prior version delivered it). Consumer repos invoke via `uv run --project D:/_code/will python D:/_code/will/tools/ingest.py <source>`.
- [ ] **`desktop-homelab` project.** `projects/desktop-homelab/` created 2026-05-09 from template. Goal: convert the X299 desktop from Windows 10 to Ubuntu 24.04, expose existing storage as family-shared Samba NAS, host Navidrome music streaming for phone-via-BT-to-car, and run Claude Code as a long-running tmux session reachable over Tailscale from phone and laptop. Phases 01-research and 02-requirements completed in conversation; ADRs 0001–0004 written for distro / mesh / NAS / music decisions. **Next:** phase 03-specification — Samba share layout, Navidrome library structure, hostnames on the mesh, user-facing CLI surface. Open: NAS disk redundancy, headless vs. desktop boot, backup destination.
- [ ] **`email-connector` project (parked).** `projects/email-connector/` created 2026-04-27 from template. Goal: capability in `will` to read the user's email so newsletter/research mail can be auto-ingested. Code+skill+setup live in `will/`; credentials+mailbox URIs+OAuth tokens live in `will-personal/`. No driving deadline — start with phase 01-research when picked up. Likely strong overlap with the agent-scheduling Google OAuth slice (25–28) — both will need a Google client setup, so coordinate so credentials are obtained once.
- [x] **Auto-improve principle for ingest tooling** — superseded by the 3x-demonstrated item below, now written up at `system/auto-improve.md`. (from money session 2026-04-27, closed 2026-06-13)
- [ ] **Status-flipping living-doc pattern** (sections move from `open` to `resolved YYYY-MM-DD` with stated rule, evidence accumulated pre-resolution) is generalizable. Reference impl: `money/research/investment-strategy.md`. If a 2nd domain adopts it (health strategy? writing process?), graduate to a system convention. (from money session 2026-04-27)
- [x] **Rename `health-ingest` plugin to `ingest`.** DONE 2026-05-17 — done at the same time as the ingest-tooling graduation (above), since both shipped together. Restart Claude Code to pick up the new plugin name. Future skills for ingest-positions / ingest-emails can join this plugin under `will/plugins/ingest/skills/`.
- [x] **Auto-improve principle now demonstrated 3x** — DONE 2026-06-13. Written up at `system/auto-improve.md`. 3 instances: papers (clean_md profiles), positions (parser fix candidate), prices (CUSIP override candidates). Pattern: tools surface improvement candidates, never auto-apply. (from money session 2026-04-28, closed 2026-06-13)
- [ ] **Pivot views via Excel Table with auto-filter** is a tooling pattern that may apply across repos. Reference impl planned at `money/tools/xlsx-export-plan.md`. If a 2nd repo wants the same (writing? health?), graduate the openpyxl Excel-Table helper to `will/tools/`. (from money session 2026-04-28)
- [ ] **The "no-pipe" rule for tool calls** is specific to projects using a `Bash(uv run python tools/:*)`-style allowlist (which is several repos by now). The matcher splits on `|` / `>` / `2>&1` — adding pipes to a tool invocation triggers a permission prompt every time. Worth a note in `will/system/` about how project allowlists interact with compound shells, so the convention propagates. (from money session 2026-04-28)
- [ ] **Project genesis modes are plural** — desktop-homelab proved the template handles **conversation-first** project creation as a 2nd successful genesis mode (after agent-scheduling's doc-migration-first). After a 3rd project uses the template (any mode), `/project` skill graduation per rule of 3 is justified. Strengthens the existing "5-phase template is diagnostically valuable" item. (from will session 2026-05-09)
- [ ] **ADRs-while-fresh pattern.** When infrastructure choices land via a discussion that already resolved requirements, write ADRs immediately rather than deferring to phase 04-design. Reference impl: desktop-homelab ADRs 0001–0004 (2026-05-09). The agent-scheduling rule "don't jump to architecture before requirements" still applies; this is downstream of resolved requirements, not a violation. Worth a note in the template's ADR README once a 3rd instance lands. (from will session 2026-05-09)
- [ ] **safe_copytree is a generic pattern.** Real Windows trees break `shutil.copytree` on reparse points (junctions, cloud placeholders), access-denied subdirs, and file sources. Per-file try/except + reparse-point skip + idempotent size-match is the right shape. Reference impl: `projects/desktop-homelab/tools/drive_migration_stage.py` 2026-05-10. After a 2nd use case (likely Phase B finalize script, or any future migration), graduate to `will/tools/safe_copy.py`. (from will session 2026-05-10)
- [ ] **Fnmatch-on-basenames is the exclude convention.** Path-style patterns (`"AppData\\Local"`) silently never match in the `matches()` helper used by the migration script. Write basename patterns. Worth a note in a tooling-conventions doc when one is written. Cost this session: ~4 min wasted I/O + a debugging round. (from will session 2026-05-10)
- [ ] **Multi-section summaries need a self-consistency pass.** When a single message contains cross-referenced facts (drive layouts, mount points, install targets), all sections must agree. Shipped a self-contradicting summary 2026-05-10 (drive layout said C:=Linux root, next-steps said install on F:); Chip caught it. Final-pass review is the fix. Could be tooled later (sanity check that drive-letter references in a doc agree on roles). (from will session 2026-05-10)
- [ ] **Autonomous-build pattern transfers from TDD to migrations.** Same shape: pre-flight → walk steps → commit per logical unit → stop at boundary → STATUS writeup. Phase A migration was the 2nd instance after agent-scheduling phases 1–3. After a 3rd domain uses it (content migration in money/health, etc.), generalize to `will/system/autonomous-build.md` as previously planned. (from will session 2026-05-10)
- [ ] **Skill-description-vs-code parity is a real anti-pattern.** Caught 2026-05-17 — `ingest-paper` SKILL.md described clean_md integration in detail (with sample stderr output, "extend, don't hand-edit" guidance) but neither `health/tools/ingest.py` nor `money/tools/ingest.py` actually called clean_md. The unified `will/tools/ingest.py` now does. Convention worth memorializing: when a SKILL.md describes code behavior, the code must exhibit it OR the description must say "planned, not yet implemented." If a 2nd instance lands, write `will/system/skill-code-parity.md`. (from will session 2026-05-17)
- [x] **Archive.org-via-curl fallback** — DONE 2026-06-13. Added as step 3e in `ingest-paper` SKILL.md. (from will session 2026-05-17, closed 2026-06-13)
- [ ] **Tool+skill pattern is now demonstrated 2x with full pair**: `commit-push` (tool + skill at `will/`) and `ingest` (tool + skill at `will/`, graduated this session). Plus `revert_ingest.py` as a tool-only candidate. After a 3rd full pair lands, write `will/system/tool-skill-pairs.md`. (consolidates earlier carry-forward; 2x as of 2026-05-17)
- [ ] **Project genesis modes — `home` is a 3rd mode**: bare-repo, no template. Life-domain repos (parallel to health/money/writing/vibedaw) don't follow `projects/_template/` — they're not software projects. Worth noting in the eventual `/project` skill spec that the template is for software projects only. (from will session 2026-05-17)
- [ ] **New life-domain repo: `home`** (ChipJust/home, private, single-repo no -personal split). Stewardship of Austin property: pest control (DE + FSL + Cedarcide), garden reclamation, planting research, permaculture. 15 sources ingested across batches 1+2. Plant-interests framework refined 2026-05-24 in `plans/plant-interests.md` (hard rules: no toxic, no chemical defaults, no managed-services deps; 8 criteria). Property mapping bootstrapped 2026-05-24 (TCAD polygon + USGS LIDAR fetch tool). Confirm/refine framing across further batches.
- [x] **Skill-vs-tool popup pattern — written up 2026-06-13.** Convention at `system/skill-tool-popup-pattern.md`. 3 instances: clean_md graduation (2026-05-17), YouTube title baking (2026-05-24), PDF URL detection (2026-06-13 — also fixed in `ingest.py` this session). Pattern: deterministic pre-steps in skill docs → move inside the tool. (from home session 2026-05-31, closed 2026-06-13)
- [ ] **`data/` convention for large geospatial / binary data** — gitignore by file extension (`*.laz`, `*.las`, `*.tif`, `*.tiff` and `data/**/lidar/`, `data/**/derived/`), commit small structured data (boundaries .geojson, attribute tables) alongside. Reference impl: `home/data/property-map/` 2026-05-24. If a 2nd repo needs the same shape (money for binary OHLC caches? health for DICOM?), graduate to a system convention in `will/system/`. (from home session 2026-05-24)
- [ ] **Plugin rename → restart-required for skill-name visibility.** After a plugin rename, the session's skill registry shows OLD name even though `installed_plugins.json` and underlying machinery use the NEW name. Demonstrated 2026-05-24 with `health-ingest:ingest-paper` lingering a week post-rename. **Workaround:** call the underlying tool directly (`uv run --project D:/_code/will python D:/_code/will/tools/...`). Worth a one-liner in this HANDOFF (or a system note) so future agents don't get caught the same way. If it recurs, document. (from home session 2026-05-24)
- [ ] **Stewardship-repo "design frame" doc pattern is emerging.** First instance: `home/plans/design-process.md` (2026-05-25, Beaudry's 7-step LA frame Mindset→Planning→Plants). Money has the analog in `research/investment-strategy.md` (a decision-contract pattern — different framing but same shape: a master plan doc that codifies a domain expert's process model and indexes per-step artifacts). 2 instances under different framings; watch for a 3rd in health/writing/vibedaw to crystallize the name and graduate to `will/system/`. (from home session 2026-05-25)
- [ ] **The "doubly load-bearing intermediate" pattern.** When two distant downstream features both consume the same derived artifact, build the artifact once as a shared substrate. Reference impl planned: `home/tools/solar_exposure.py` — a per-cell annual kWh raster derived from DEM+DSM+pvlib that feeds BOTH plant siting (step 7) AND IoT node power budget (step 6 automation layer). Not novel as a general software pattern, but worth surfacing as an explicit design move for tool authoring — name the shared substrate early so it gets built once, not twice with slight differences. Single instance so far; revisit after a 2nd. (from home session 2026-05-25)
- [ ] **Goals/plans split is a new structural pattern in stewardship repos.** First instance: home's `goals/` + `plans/` 2026-05-31. Goals = WHY/WHAT (intent + verb taxonomy ELIMINATE/CONTROL/MANAGE + sub-goal tree with cross-links and evidence base); plans = HOW (implementation artifacts that serve specific sub-goals). Each goal/plan cross-references the other directionally. Negative-frame (suppression) and positive-frame (cultivation) goals live in separate files even when content overlaps, because mixing them is a real failure mode. Single instance; watch for a 2nd in health/money/writing/vibedaw before graduating the convention to `will/system/`. (from home session 2026-05-31)
- [ ] **Research-agent → evidence-assessment → goal-revision is a workflow pattern.** When commissioning research, ask the agent for an *honest evidence assessment*, not just a source compilation. Reference impl: snake-ecology research agent (2026-05-31) returned URLs grouped by authority PLUS a 2–3-sentence "what the literature actually says" summary distinguishing well-supported claims (king-snake predation on rattlesnakes via venom immunity) from folk ecology (rat-snake displacement of rattlesnakes). The evidence assessment was the actionable output that drove the goal-doc revision; the URL list was scaffolding. Single instance; revisit pattern after a 2nd lands. (from home session 2026-05-31)
- [ ] **Parallel-Bash sibling-cancellation on first failure** is a harness behavior. When firing multiple Bash tool calls in parallel, one error cancels the rest. Workaround: chain commands with `;` in a single Bash call when the operations are independent but you want failures to NOT cascade-cancel siblings. Reference: snake-research ingest batch (2026-05-31) — 11 parallel ingest calls had 3 complete before a PDF-URL failure cancelled 7 others; chained `;` retry of the remaining 7 worked cleanly. Worth a note in a tooling-conventions doc when one is written. (from home session 2026-05-31)
- [ ] **Marginal-quality ingest threshold.** Current `ingest.py` writes output for quality scores as low as 60 (with a warning). Score 60 with 88 words = pure navigation chrome and should fail outright. Worth either tightening the gate to ~70 or requiring `--allow-marginal` to write the file. Small tool improvement. (from home session 2026-05-31)
- [ ] **Three.js viewer pattern (Python-generates-HTML with JS rendering) may be reusable** across repos if other domains need spatial visualization. Python encodes data as base64/JSON, JS template renders. The boundary is at data encoding, not the rendering API. Single instance (home terrain viewer, 2026-06-13); watch for 2nd. (from home session 2026-06-13)
- [ ] **pycolmap GPU support on AMD (ROCm) is experimental.** When the Linux desktop migration happens, test COLMAP dense reconstruction on the RX 7900 XTX. Fallback is CPU (~10min/object vs ~1min). Could affect home Phase B (phone capture pipeline) at scale. (from home session 2026-06-13)
