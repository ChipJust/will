# Status

**Project:** desktop-homelab
**Phase:** 05-implementation (Phase A done — pre-Linux data staging complete)
**Last action:** Phase A executed successfully 2026-05-10 07:38–07:56. **63.6 GB / 328,771 files staged on E:\\_migration\\.** 27/27 copy actions complete, 0 errored. Two runs needed — first run hit shutil.copytree brittleness on reparse points (junctions, OneDrive cloud placeholders), access-denied subdirs, and a file source (.gitconfig); fixed script with safe_copytree (tolerates errors per-file, skips reparse points, idempotent on re-run via size-match), fixed plan exclude pattern (basename matching, not path matching); re-ran clean.
**Next action:** Chip's call — proceed to physical Linux install (Ubuntu 24.04 LTS USB → F: SATA SSD). Pre-install checklist: external USB backup of irreplaceables (Tax/Medical/Legal/photos); BIOS check (CSM off, Secure Boot off); USB installer prepared. Phase B (post-install Python script) drafted next session.
**Drive layout (revised 2026-05-10 per Chip):**
- C: NVMe 477GB → Linux root + /home (ext4)
- D: NVMe 477GB → /workspace, ext4 conversion last (active dev work mounted)
- E: HDD 2.8TB → /srv/nas, **NTFS kept** (long-term family storage)
- F: SATA SSD 224GB → /srv/media, ext4 (music + voice memos, fast random access)
**Open questions:**
- Disk redundancy for NAS — single 3TB vs. mirror pair? (deferred to Phase B)
- Headless boot vs. GNOME/Plasma desktop session? (deferred to Phase B)
- Backup destination for irreplaceable family data (deferred — separate follow-on project candidate)
- Final NAS folder structure on E: (consolidate D:/E: duplicates: _code, Music, Reaper, Timothy J. Keller, pictures/photos, Insurance/Medical/Legal/Money) — Phase B
**Blockers:** none — Phase A running; Phase B blocked on physical Linux install
**Updated:** 2026-05-10
