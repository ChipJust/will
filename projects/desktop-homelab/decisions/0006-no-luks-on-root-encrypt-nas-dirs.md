# 0006. No LUKS on root; encrypt sensitive NAS directories instead

Status: Accepted (2026-10-07)

## Context

Ubuntu's installer offers LUKS full-disk encryption as an install-time checkbox. It
cannot be retrofitted without a reinstall, so it had to be decided before the install
rather than deferred with the other Phase B questions.

What LUKS actually buys is narrower than its reputation suggests:

- **Protects against:** physical theft of the machine or the drive — someone pulling the
  disk and reading it in another computer.
- **Does not protect against:** anything while the machine is running and unlocked. The
  volume is decrypted for the entire uptime of an always-on box. Malware, remote
  compromise, and anyone at the logged-in desktop are all unaffected.

Against that, the costs land directly on this project's goals:

- Every boot halts at a passphrase prompt before the OS starts. This desktop is meant to
  be an always-on homelab serving Samba and Navidrome and reachable over Tailscale
  (ADRs 0002–0004). Any unattended reboot — power blip, kernel update — takes the NAS
  and music server down until someone physically walks over and types a passphrase.
- It collides with the still-open "headless boot vs. desktop session" question in
  STATUS.md, effectively pre-deciding it in the less convenient direction.
- TPM/Clevis auto-unlock removes the prompt, but adds setup work and weakens the
  guarantee — the key then lives inside the machine being protected.

The decisive point: **LUKS on root would not have covered the data that matters anyway.**
The sensitive family documents (Tax, Medical, Legal) live on E:, the 2.8 TB NAS volume,
which stays NTFS and is a separate disk from the encrypted root. The threat model and the
control were aimed at different drives.

This is a desktop that sits in a house and does not travel. Physical theft is the lowest-
probability item in its threat model, and remote exposure — the highest — is already
addressed by ADR 0002's Tailscale-only posture.

## Decision

**Do not enable LUKS** on the root disk at install time.

Instead, in Phase B, encrypt the specific NAS directories holding sensitive family
documents using `gocryptfs` or `fscrypt` — filesystem-level encryption over the
Tax / Medical / Legal trees on `/srv/nas`.

## Consequences

- Unattended reboot works. The homelab comes back up on its own after a power event or an
  automatic kernel update, which is a prerequisite for the always-on goal.
- The "headless boot vs. desktop session" question stays genuinely open instead of being
  settled by a side effect.
- **Phase B obligation:** directory-level encryption for sensitive NAS data is now a
  committed work item, not an optional extra. If it is skipped, this ADR's reasoning does
  not hold and the machine ends up with less protection than the LUKS option would have
  given, not more. Track it in Phase B.
- Physical theft of the desktop exposes the root disk. Accepted — the machine does not
  leave the house, and the high-value data is on E:, which the Phase B work covers.
- Reversing this requires a full reinstall. Revisit only if the machine's role changes
  (moves off-site, becomes portable, or starts holding data with a regulatory obligation).
