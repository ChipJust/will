# will — System Handoff
*Last updated: 2026-04-12*

This is the system-level context loaded by `/wake` before any subject-repo briefing.
It re-establishes the architecture and cross-cutting state of the whole ecosystem.

---

## The system in one paragraph

Chip is building a multi-repo AI agent ecosystem — one repo per life context (health,
money, writing, music, etc.), with `will` as the meta-agent that manages all of them.
Each subject repo is self-contained: its own tooling, its own CLAUDE.md, its own
ORIENTATION.md and HANDOFF.md. Skills and practices (ingest pipeline, reflect, wake)
originate in `will` and are copied into subject repos as needed. The goal is an
AI-assisted operating system for intentional living, grounded in Christian values.

---

## Repo ecosystem — current state

| Repo | Status | What it does |
|------|--------|-------------|
| `will` | Active | Public framework: plugins, bootstrap, conventions |
| `will-personal` | Active | Private layer: config, reflections, problems, hardware tracking |
| `health` | Active | Health research framework: ingest tooling, research refs |
| `health-personal` | Active | Personal health data: Chip's records, Paige's profile (in progress) |
| `money` | Active | Investment research, financial + social-impact analysis |
| `writing` | Active | Markdown documents written collaboratively |
| `vibedaw` | Active | Music context agent |
| `giving` | Planned | Charitable giving tracking and research |
| `prayer` | Planned | Prayer request log and follow-up |
| `social-influence` | Planned | Policy advocacy and social media strategy |

---

## Cross-cutting concerns (read before working in any repo)

**Python:** Now on 3.14.3 (uv-managed). `python` and `python3` both resolve to it
via `~/.bashrc`. To upgrade: `uv python install 3.X` + update one line in `~/.bashrc`.

**Windows/Linux:** Currently on Windows 10 Pro. Linux migration is the recommended path
for AI hardware support (AMD ROCm, Tenstorrent). See `will-personal/system/hardware.md`
and `will-personal/hardware/projects/2026-hardware-refresh.md`.
All tools are written to be portable — UTF-8 stdout wrappers, forward-slash paths in bash.

**AMD:** Chip works for AMD. Always prefer AMD CPU/GPU in hardware recommendations.
No Intel CPU options unless explicitly requested.

**Encoding:** Any Python script that writes text must wrap stdout in UTF-8.
Windows cp1252 silently corrupts special characters. This is a known gotcha.

**Commit style:** "commit" = stage specific files + commit + push. No prompts.
Never `git add -A`. Never commit PDFs, `.venv/`, `egg-info/`, or `output/`.

**Plugin install:** After adding or modifying a plugin in `will/plugins/`, run
`bash plugins/install.sh` from the will repo root, then restart Claude Code.

**Hardware tracking:** Machine records and purchase history live in
`will-personal/hardware/machines/` (one file per machine). Project files in
`will-personal/hardware/projects/`. Serial numbers and invoices go there, not in `will`.

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
- [ ] Modernize HANDOFF.md in `money`, `writing`, `vibedaw` — strip cross-cutting sections (now in will-personal Layer 2); follow the health pattern from 2026-04-10
- [ ] Add `hardware/` tracking pattern to will PLAN.md (new content category in will-personal, from 2026-04-12 session)
