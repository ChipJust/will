# 0002. Use Tailscale for cross-device mesh networking

Status: Accepted (2026-05-09)

## Context

Chip wants his desktop, laptop, and phone reachable to each other regardless of which network they're on, with no public-internet exposure of the desktop's services. The "no Microsoft services" constraint applies. Family devices that need only LAN access are out of scope for this layer.

Options considered:
- **Tailscale** — managed WireGuard mesh, MagicDNS for stable hostnames, free for personal use, not Microsoft, not Google. Coordination server holds key exchange and ACL metadata only; traffic is direct peer-to-peer.
- **Headscale** — self-hosted Tailscale-compatible coordination server. More control, more setup, more to maintain.
- **Plain WireGuard** — manual peer config per device, no service discovery, must be redone when devices change.
- **OpenVPN / IPsec** — older, heavier, no mesh model, not pleasant on mobile.

Tailscale's coordination dependency (controlplane.tailscale.com) is acceptable risk for personal use. Migration to Headscale later preserves device identity and ACL semantics.

## Decision

Start with **Tailscale** (free tier). Migrate to **Headscale** later if the coordination dependency becomes a concern.

## Consequences

- Devices get stable hostnames (e.g. `desktop`, `laptop`, `phone`) regardless of which network they're on.
- All non-LAN access to homelab services traverses Tailscale; no port-forwarding on the home router; no public-internet exposure.
- Adding a new device = install client + log in; no peer-config edits anywhere else.
- Family devices that don't need outside-LAN access (mom's laptop, occasional family clients) don't need Tailscale at all — they hit the NAS over LAN.
- Migration to self-hosted Headscale preserves devices and ACLs if the upstream dependency becomes unacceptable.
