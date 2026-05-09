# 0001. Use Ubuntu 24.04 LTS as the base operating system

Status: Accepted (2026-05-09)

## Context

The desktop will replace Windows 10 with Linux. The chosen distro affects:
- Driver/firmware compatibility for current and planned hardware (GTX 1650 today; planned RX 7900 XTX; possible Tenstorrent Wormhole later)
- Maturity of the AI tooling stack (ROCm, CUDA, llama.cpp, Docker)
- Upgrade cadence and stability expectations
- Community size for troubleshooting

Real candidates considered:
- **Ubuntu 24.04 LTS** — Tier-1 platform for AMD ROCm, Tenstorrent's official support target, 5-year support window.
- **Fedora 41/42** — newer kernels, upstream-aligned, no Snap. ROCm works but isn't the reference platform; 13-month release cycle increases upgrade churn.
- **Arch / EndeavourOS** — bleeding edge, every AI tool packaged in AUR, but high maintenance burden and breakage risk.
- **NixOS** — declarative and reproducible, philosophically aligned with an agent-managed system, but steep learning curve will eat weeks before delivering value.

The "no Microsoft" constraint is satisfied by any Linux distro. Canonical is not Microsoft, and Snap (the most-cited Ubuntu objection) is removable via `apt purge snapd`.

## Decision

Use **Ubuntu 24.04 LTS** with the HWE kernel track for current AI hardware support and a 5-year stability runway.

## Consequences

- ROCm and Tenstorrent installs follow vendor-supported paths; no yak-shaving on driver builds.
- 5-year LTS = no major OS upgrade for the project's expected lifetime.
- Snap will be present by default. If it gets in the way, removal is one command.
- If the philosophical pull to Fedora becomes important later, distro switch is non-trivial but recoverable — config and data both portable, Docker services trivially so.
- Community-written homelab documentation is overwhelmingly Ubuntu-flavored, reducing setup friction.
