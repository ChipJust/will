# 02 — Requirements

## Prompt

You are entering the requirements phase.

**Goal:** Capture *what* the system must do and for whom, in language that doesn't pre-judge the design.

**Activities:**
- **Users / actors.** Who interacts with this? What is their context (device, attention level, expertise)?
- **Behavior list.** Bullet list of capabilities, each phrased as a user-facing outcome ("the user can …", "the system records …"). One bullet per capability; nest sub-points if needed.
- **Success criteria.** How do we know it's working? Quantitative where possible (latency, accuracy, cost).
- **Non-functional requirements.** Performance, privacy, cost ceiling, availability, observability, accessibility.
- **Explicit non-goals.** Things this does *not* try to do — write them down so design doesn't drift into them.

**Exit criteria:**
- An implementer who never read the research could write the spec from this file.
- Each requirement is independently checkable.

**Out of scope:**
- API/protocol details (that's `03-specification`).
- Internal structure (that's `04-design`).

---

## Saved response

*Filled 2026-05-09.*

### Users / actors

- **Chip (primary).** Engineer, comfortable with shell and self-hosting. Uses desktop for AI work, laptop for travel, phone in car and on-the-go. Wants reproducibility and minimal ongoing maintenance.
- **Wife.** Will need read/write access to family file share. Phone-primary user.
- **Mom.** Windows laptop user. NAS must "just appear" as a network drive with no setup help beyond credentials. Low friction tolerance.
- **Other family.** Read access to specific shared folders (photos, household docs). Occasional usage.

### Behaviors

**Operating system:**
- Desktop runs Linux as the primary OS, replacing Windows 10.
- Chip can SSH into the desktop from any of his devices, and the session survives disconnects.
- A Claude Code session can run on the desktop continuously and be re-attached from any of Chip's devices.

**Cross-device networking:**
- All Chip's devices (desktop, laptop, phone) are reachable to each other by stable hostname regardless of which network they're on.
- Desktop services are accessible to Chip's laptop and phone from outside the LAN, but not exposed to the public internet.
- Family devices reach the NAS over the LAN; outside-LAN access is not required for them.

**Phone ↔ desktop integration:**
- The phone can mirror notifications to the desktop and vice versa.
- Clipboard syncs between phone and desktop.
- Files can be sent from phone to desktop in one tap.

**Network-attached storage:**
- The desktop exposes named shares to all family devices over the local network.
- Mom's Windows laptop can mount a share as a drive letter without manual setup beyond entering credentials.
- Chip's laptop can read/write the shares from outside the LAN over the mesh network.
- Phones can browse and play files from the shares on the LAN.
- Each share has its own access list — family-wide vs. Chip-only vs. read-only-for-others.

**Music streaming:**
- Chip's phone can stream the MP3 library from the desktop while at home (LAN), away (mesh), or in the car (offline cache).
- A Subsonic-API client on the phone connects to the music server and lists albums/artists/playlists.
- Chip can pin specific playlists for offline listening before driving out of coverage.
- Phone audio over Bluetooth to the car works transparently — the car sees "phone is playing audio."
- The library auto-indexes when MP3s are added to the music share.

**Service durability:**
- All services restart automatically on reboot.
- A power blip or kernel update does not require manual intervention to bring NAS or music back.
- Service health is observable from the desktop without external monitoring tools (e.g., systemd status, container logs).

### Success criteria

- **Migration complete:** all of Chip's existing dev workflows (Claude Code, repos, uv, git) function on Linux at parity with Windows. No Windows boot needed for daily work for 30 consecutive days.
- **NAS adoption:** mom is using the NAS for at least one regular file (e.g., QuickBooks backup) within 30 days of setup.
- **Music in car:** Chip plays a pinned playlist over BT in the car, away from any wifi, in one drive without skips or audio dropouts attributable to the source.
- **Phone-as-terminal:** Chip starts or resumes a Claude session from his phone on cellular at least once successfully.
- **Reachability:** desktop is reachable by stable hostname from all Chip's devices, on any network, with no manual reconfiguration when networks change.
- **Maintenance:** less than 1 hour of routine maintenance per month over the first 6 months.

### Non-functional requirements

- **Privacy:** no telemetry-by-default services. No third-party SaaS for core function (NAS, music). The mesh-network coordination dependency (Tailscale) is acceptable; self-hosting (Headscale) is a reversible upgrade.
- **Reliability:** core services survive reboots and kernel updates without manual intervention.
- **Maintenance budget:** Chip should not spend more than ~1 hour/month on routine maintenance.
- **Power:** machine running 24/7 is acceptable; idle draw measured post-migration to inform future decisions about wake-on-LAN.
- **Cost:** software stack is free + open-source. Hardware additions limited to drives/cables in this project. GPU upgrade is tracked separately.
- **Security:** no service exposed to the public internet. SSH key-only login. Samba shares require auth (no anonymous shares). Distinct local users for distinct access tiers.

### Explicit non-goals

- **No public-internet hosting.** This is a private home server, not a self-hosted SaaS for the world.
- **No declarative/reproducible OS config (e.g., NixOS).** Imperative + documentation is enough at this scale.
- **No high-availability or clustering.** One machine. If it's down, family loses access until Chip fixes it.
- **No video streaming yet.** Music is the only media surface in scope. Video can layer in later (Jellyfin alongside Navidrome) but is not part of this project.
- **No automated cloud backup yet.** Backup strategy is acknowledged as open and deferred to a follow-on.
- **No phone-as-NAS-client for everyday writes.** Phones can browse + play, but the primary write path is desktop/laptop.
- **No replacement of mom's email or other primary cloud services.** Just NAS access.
- **No replacement of Google ecosystem on the phone.** Pixel 7 stays as-is; "no Microsoft" is the constraint, not "no third-party services."
