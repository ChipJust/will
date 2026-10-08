# Status

**Project:** desktop-homelab
**Phase:** 05-implementation (Phase A done — pre-Linux data staging complete)
**Last action:** Phase A executed successfully 2026-05-10 07:38–07:56. **63.6 GB / 328,771 files staged on E:\\_migration\\.** 27/27 copy actions complete, 0 errored. Two runs needed — first run hit shutil.copytree brittleness on reparse points (junctions, OneDrive cloud placeholders), access-denied subdirs, and a file source (.gitconfig); fixed script with safe_copytree (tolerates errors per-file, skips reparse points, idempotent on re-run via size-match), fixed plan exclude pattern (basename matching, not path matching); re-ran clean.
**Next action:** Physical Linux install (**Ubuntu 26.04.1 LTS** USB → **C: NVMe**, wipes current Windows). Distro revised 2026-10-07 — see ADR 0005, which supersedes 0001. F: SATA SSD will be wiped + reformatted to ext4 for /srv/media in Phase B, not the install target. Phase B (post-install Python script) drafted next session.

**Pre-install checklist (as of 2026-10-07):**
- [ ] **External USB backup of irreplaceables** (Tax/Medical/Legal/photos) to the USB HDD — the one on-machine copy on E: is not a backup
- [ ] **Re-stage C:** — `E:\_migration\C-chipj` is from 2026-05-10; ~5 months of drift (`.claude`, `Downloads`, `.ssh`, browser profiles). `drive_migration_stage.py` is idempotent on size-match, so it copies only the delta
- [ ] Inventory C:-only items: license keys, saved Wi-Fi/VPN creds, `AppData` config
- [ ] Record Windows product key (`wmic path SoftwareLicensingService get OA3xOriginalProductKey`) for rollback
- [ ] BIOS: CSM off, Secure Boot off (firmware confirmed UEFI 2026-10-07)
- [x] USB installer stick identified — Disk 4, Silicon Power 32 GB, H:, FAT32, empty
- [x] ISO downloaded + SHA256 verified — `ubuntu-26.04.1-desktop-amd64.iso` at `C:\Users\chipj\Downloads\`, 6.04 GB, sum matches Canonical
- [x] Writer tool — `rufus-4.15p.exe` (portable) in `Downloads\`, Authenticode signature valid (Akeo Consulting)
- [x] **LUKS decided: no** — see ADR 0006. Carries a Phase B obligation to encrypt sensitive NAS dirs instead
- [ ] Write ISO to H: with Rufus, then run "Check disc for defects" from the boot menu before committing
- [ ] Verify no credential dirs reappear before wipe — `.ssh`, `.gnupg`, `.aws`, `.docker`, `.netrc`, `.git-credentials`, `.npmrc` all confirmed absent 2026-10-07 (`gh` token is inside `AppData\Roaming`, which IS staged)

**Security posture (decided 2026-10-07, replaces Windows AV):** no antivirus for host protection. Install from apt/signed vendor repos only; `unattended-upgrades` on; UFW default-deny inbound; services reachable **only** over Tailscale (never port-forwarded); SSH key-only. ClamAV is Phase B and scoped to scanning `/srv/nas` so the share doesn't carry Windows/Mac malware to family machines — file-server hygiene, not host defense. Backups are the real ransomware control, which makes the deferred backup-destination question below load-bearing.
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
**Blockers:** none — Phase B blocked on physical Linux install
**Updated:** 2026-10-07
