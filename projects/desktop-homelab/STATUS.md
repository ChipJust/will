# Status

**Project:** desktop-homelab
**Phase:** 03-specification (entering)
**Last action:** Completed 01-research and 02-requirements; wrote ADRs 0001–0004 capturing the load-bearing tech choices already locked in via discussion (distro, mesh network, NAS protocol, music server).
**Next action:** Define the externally observable behavior — Samba share layout and permissions, Navidrome library structure, hostnames on the Tailscale mesh, and the user-facing CLI surface for managing services on the desktop.
**Open questions:**
- Disk redundancy for NAS — single 3TB vs. mirror pair? (deferred to phase 04)
- Headless boot vs. GNOME/Plasma desktop session? (deferred to phase 04)
- Backup destination for irreplaceable family data (deferred — separate follow-on project candidate)
- Whether to consolidate 2× 512GB NVMe usage now or after first-month measurements
**Blockers:** none
**Updated:** 2026-05-09
