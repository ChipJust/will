# will

A framework for running your life with AI assistance.

**will** is the meta-agent — a public template for building a multi-repo system where
each repository is an AI agent representing a specific life context. Clone this repo,
fill in your config, run the bootstrap, and you get the same infrastructure with none
of the personal content.

---

## Concept

Each repo is an **agent** with its own purpose:

| Repo | Example intent |
|------|---------------|
| `will` | Meta-agent. Owns the infrastructure. You're looking at it. |
| `health` | Health research, supplement stack, lab tracking |
| `money` | Personal finance and values-based investment research |
| `writing` | Writing projects and notes |
| `music` | Music production and theory |
| `giving` | Charitable giving and stewardship |
| `prayer` | Prayer tracking and follow-up |
| _your context_ | Whatever matters to you |

Each agent has:
- A `CLAUDE.md` tailored to its context
- Ingested references in `research/refs/` (papers, articles, transcripts)
- Ingest tooling that processes PDF, DOCX, VTT, and HTML into versioned markdown
- A session reflection practice (`/reflect`) for continuous improvement

The **will** repo sees across all agents and improves the whole system.

---

## Getting started

**1. Clone this repo**
```bash
gh repo clone <your-fork>/will
cd will
```

**2. Create your config**
```bash
cp config.example.json config.json
# Edit config.json: your name, email, GitHub username, workspace path, repo list
```

**3. Run bootstrap**

Linux:
```bash
bash bootstrap/setup.sh
```

Windows (PowerShell as Administrator):
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\bootstrap\setup.ps1
```

The bootstrap installs all tools, clones your repos, runs `uv sync`, and installs
the Claude Code plugins that make the agents work.

---

## What you get

- **Git, gh, uv, Node.js, Claude Code** — all installed and configured
- **All your repos** cloned to your workspace
- **Claude Code plugins** installed:
  - `ingest-paper` — converts research papers/transcripts to versioned markdown
  - `reflect` — end-of-session reflection skill that builds institutional memory
- **Android device integration** — ADB and KDE Connect for phone-desktop workflow

---

## Plugins

Custom Claude Code skills live in `plugins/`. Install them anytime:

```bash
bash plugins/install.sh   # Linux
.\plugins\install.ps1     # Windows
```

---

## Personal content

Your reflections, problems, notes, and private configs are **not** in this repo.
Store them in:
- `personal/` (gitignored, local only), or
- A separate private repo that you add to your `config.json` repo list

The framework is public. Your life is yours.

---

## System conventions

See `system/conventions.md` for the working rules that apply across all agents.

---

## Philosophy

This system is designed to be a tool, not a cage. The repos, skills, and conventions
exist to reduce friction and build accumulated knowledge — not to be followed for their
own sake. Adapt freely.
