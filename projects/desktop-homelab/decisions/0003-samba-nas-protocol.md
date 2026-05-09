# 0003. Use Samba (SMB) for NAS file sharing

Status: Accepted (2026-05-09)

## Context

The NAS must be usable by:
- Mom's Windows laptop ("appears as a network drive" with no extra software)
- Chip's Linux laptop (read/write from anywhere via Tailscale)
- Android phones (browse and play files)
- Future machines of unknown OS

Options considered:
- **SMB (Samba implementation)** — universal client support, native on Windows / macOS / Linux / Android.
- **NFS** — clean Linux-to-Linux, awkward on Windows (requires per-machine NFS client install), poor on Android.
- **WebDAV** — works everywhere over HTTP, but UX is rougher and Windows treats WebDAV folders inconsistently.
- **SSHFS** — Linux-only mount via FUSE; not viable for mom or for Android.

The "no Microsoft" constraint is about avoiding Microsoft-managed services (OneDrive, Teams, Microsoft accounts), not avoiding protocols Microsoft once authored. Samba is the open-source SMB implementation, runs on Linux, requires no Microsoft account, and has no telemetry.

## Decision

Use **Samba** to expose all NAS shares.

## Consequences

- Mom's Windows laptop can map shares as drive letters with no extra software beyond entering credentials.
- Chip's Linux laptop, Android phones, and any future Mac all work natively against the same shares.
- Authentication via local Linux users mapped into Samba; no public anonymous shares.
- Performance is fine for music streaming, family file exchange, and backups; not optimized for high-throughput parallel database workloads (out of scope).
- If a future workload needs Linux-to-Linux high-throughput, NFS can be added alongside Samba on the same data without disruption.
