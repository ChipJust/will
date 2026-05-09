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

*Filled 2026-05-09. Research conducted via discussion rather than independent agent investigation; this captures the surveyed landscape so the next phase has it cited.*

### Prior solutions surveyed

**Synology / QNAP / TrueNAS Scale (turnkey NAS appliances)**
- Pre-built NAS hardware with opinionated OS. TrueNAS Scale is the open-source variant runnable on commodity hardware.
- Nails: storage, sharing, snapshots, replication, plugin ecosystem.
- Falls short here: the desktop (i9-9960X / 128GB / X299) is overkill for a NAS appliance and underused if dedicated to one. It must also run Claude Code, future LLM workloads, and Docker services. Turnkey appliance OSes constrain non-NAS workloads.

**Plex Media Server**
- Industry leader for self-hosted media; mobile apps polished; Plexamp is the gold standard for music UX on phone.
- Falls short: proprietary, requires plex.tv account, ships telemetry by default. Conflicts with the no-managed-services stance.

**Jellyfin**
- Open-source Plex equivalent. Music + video + photos. Active community.
- Nails: feature parity with Plex on basics, no account required, fully self-hosted.
- Falls short for music-only: UX less polished than Navidrome; heavier than necessary if video isn't a goal yet.

**Navidrome (Subsonic API server)**
- Music-only, single Go binary, indexes a folder of files, serves Subsonic API.
- Nails: lightweight, focused, broad mobile client ecosystem (Symfonium, DSub, play:Sub) with strong offline cache.
- Falls short: music-only — no video/photos. Not a problem if those needs are addressed by a separate server later.

**Generic homelab patterns (Docker Compose + reverse proxy + per-service container)**
- One container per service, traefik or caddy out front, separate networks for tiers.
- Nails: clean separation, easy upgrades, declarative config, easy rollback.
- Falls short: complexity overhead is real for a single-user homelab. We can do simpler — systemd services + a couple of containers.

### Hard constraints

- **Hardware:** i9-9960X (16c/32t), 128GB DDR4, ASRock X299 Steel Legend, GTX 1650 (4GB VRAM, hard ceiling for local LLM at ~3B params Q4), 240GB SATA SSD + 2× 512GB NVMe + 3TB HGST. PCIe 3.0.
- **Family multi-platform:** mom's Windows laptop must access NAS without setup help. Phones (Android primary) must access music + NAS shares.
- **No Microsoft services:** no OneDrive, no Microsoft account, no Teams. SMB-the-protocol is permissible because the implementation (Samba) is open-source and account-free.
- **No public internet exposure:** services reachable from family devices, not from the open web. Mesh VPN solves this for Chip's devices; LAN solves it for family.
- **Always-on availability:** services should survive Chip's working hours, reboots, and kernel updates without manual intervention.
- **Budget for now:** software stack must be free + open-source. Hardware additions limited to drives/cables. RX 7900 XTX upgrade and Tenstorrent Wormhole are tracked separately.

### Open variables (genuine choices for requirements/spec)

- Single drive (current 3TB HGST) vs. mirror pair for NAS data
- Boot to console vs. boot to GNOME/Plasma — affects RAM, login UX, and whether GTX 1650 is used at all
- Wake-on-LAN vs. always-on (power cost vs. reachability)
- 2× NVMe consolidation: keep current split (workspace + AI/Docker) or rebalance after first-month measurements
- Backup destination for irreplaceable data (cloud, external drive, second machine, off-site)

### What we don't know yet (cheap-to-find)

- Idle power draw of the desktop on Linux — measure with outlet meter once migrated.
- Time-to-first-audio on phone via Tailscale from outside the LAN — test once Navidrome is up.
- Whether Symfonium offline cache holds across cellular dead zones — test on a real drive.
- Remaining life of the 3TB HGST — pull SMART data before committing as primary NAS storage.
- Linux compatibility of the X299 BIOS for clean dual-boot — verify CSM and Secure Boot settings.
