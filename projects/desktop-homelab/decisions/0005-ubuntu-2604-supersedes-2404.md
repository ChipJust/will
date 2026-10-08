# 0005. Use Ubuntu 26.04 LTS as the base operating system

Status: Accepted (2026-10-07) — supersedes [0001](0001-ubuntu-2404-base-distro.md)

## Context

ADR 0001 chose Ubuntu 24.04 LTS on 2026-05-09. At that time 26.04 LTS had only just
released (April 2026) and the governing assumption was that AMD certifies ROCm against
the *prior* LTS first — so picking the newer LTS looked like getting ahead of vendor
support on exactly the workload the machine exists for.

That assumption turned out to be wrong, and the facts moved in the opposite direction:

- **Ubuntu 26.04.1 LTS ("Resolute Raccoon")** is the current LTS, with a point release
  already shipped.
- Canonical and AMD partnered to ship **ROCm 7.1.0 in the official Ubuntu archive**.
  Install is `sudo apt install rocm`; updates and security patches flow through normal
  `apt upgrade`, and applications can pull ROCm in as an ordinary dependency. On 24.04
  the path is AMD's manual installer instead.
- AMD's own compatibility matrix lists **Ubuntu 26.04.1 (kernel GA 7.0)** as a supported
  target alongside 24.04.5 (GA 6.8) and 22.04.5 (GA 5.15).
- Canonical advertises up to 15 years of ROCm support on LTS releases under Ubuntu Pro.
- Archive-packaged ROCm continues forward through 26.10, 27.04, and beyond.

So 26.04 is not the riskier choice for AMD GPU compute — it is the better-supported one.
The decision inverted on new evidence, not on preference.

## Decision

Use **Ubuntu 26.04.1 LTS desktop** as the base operating system. Install media:
`ubuntu-26.04.1-desktop-amd64.iso`,
SHA256 `601e30fbf5d97759367c632e2c33630665039b7e2158fd068403da3ccf1bda1f`.

Desktop ISO rather than live-server: this machine replaces Chip's daily-driver Windows
desktop, so a graphical session is a requirement, not an option. The "headless boot vs.
desktop session" question in STATUS.md is about *how the homelab services run*, not about
which ISO to install — a desktop install can run headless services fine, the reverse is
more work.

## Consequences

- ROCm arrives via `apt` from a signed official repository rather than a vendor installer
  script. This is a direct win for the "install from signed repos, not `curl | bash`"
  security posture — the AI stack stops being the exception to it.
- Support runway extends to 2031 instead of 2029.
- Newer kernel (GA 7.0) means better out-of-box support for recent AMD silicon, relevant
  to the planned RX 7900 XTX.
- **Open risk — Tenstorrent.** `tt-metal`'s tested target is Ubuntu 22.04; 24.04 has
  repository packages; 26.04 is not yet documented as supported. The Wormhole n150d is a
  future purchase, not owned hardware, so this is not blocking today and support will
  likely land before the card does. If it does not, the card can be driven from a
  container or a dedicated 22.04/24.04 install rather than dictating the host OS.
- ADR 0001's reasoning about Snap, Fedora, Arch, and NixOS still stands unchanged — only
  the Ubuntu version is revised. `apt purge snapd` remains available.

## Note on the reversal

ADR 0001's error was not the conclusion but the unverified premise — "AMD certifies the
prior LTS first" was asserted from general industry pattern rather than checked against
AMD's published compatibility matrix. Worth remembering that vendor support claims in an
ADR should cite the matrix, not the pattern.
