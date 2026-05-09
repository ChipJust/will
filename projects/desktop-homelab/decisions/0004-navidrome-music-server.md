# 0004. Use Navidrome for music streaming, Symfonium on phone

Status: Accepted (2026-05-09)

## Context

Chip wants to stream his MP3 library from the desktop to his phone (then via Bluetooth to the car), with offline cache support for driving outside coverage. The "no Microsoft / no proprietary lock-in" constraint applies.

Options considered:
- **Plex** — most polished mobile UX (Plexamp), but requires plex.tv account, ships telemetry by default, proprietary.
- **Jellyfin** — open-source Plex equivalent. Music + video + photos. Heavier; music UX less polished than Navidrome.
- **Navidrome** — music-only, single Go binary, indexes a folder, serves Subsonic API. Wide ecosystem of mobile clients.
- **Just SMB the music folder, play in VLC / Foobar2000 mobile** — no streaming server. No offline-cache UX, no metadata browse, breaks down outside the LAN.

The phone client matters as much as the server. **Symfonium** ($6 one-time, no subscription) is the recommended Android client for the Subsonic API: well-engineered offline cache, queue management built for driving. **DSub** is the free fallback if cost is a concern (less polished).

## Decision

Use **Navidrome** as the music server, paired with **Symfonium** on the phone.

## Consequences

- Music UX is purpose-built for the goal (driving + Bluetooth to car).
- No video / photos in scope under this server. If those are wanted later, Jellyfin can be added alongside Navidrome — they don't conflict.
- One-time $6 cost for Symfonium; the alternative (free DSub) works but is rougher.
- Subsonic API is wide-ecosystem, so the phone client is replaceable without changing the server.
- Music files live in a Samba share so adding tracks is just "drop files in the share" — Navidrome auto-indexes.
