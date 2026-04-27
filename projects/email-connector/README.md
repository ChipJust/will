# email-connector

A capability for `will` to read the user's email — primarily so research that arrives by mail (e.g. Bravos updates, Taylor Dart articles, paid newsletters) can be ingested without manual download → save → drop-in. The connector is designed to be reusable across topic repos (`money`, `health`, etc.) the same way the `ingest-paper` skill is.

**Cross-repo split:**
- `will/` (this repo) — the connector code, the skill, setup instructions, ADRs, and any logic that doesn't depend on a specific user's account.
- `will-personal/` — the user's actual credentials, mailbox URIs, OAuth client config, refresh tokens, label/folder names, account-specific filters. Anything that names a real account or exposes a secret.

**Status:** parked. Created 2026-04-27 as a placeholder. Walk forward from `STATUS.md` when picking it up.

## Quick links

- [STATUS.md](STATUS.md) — current phase and next action
- [01-research.md](01-research.md)
- [02-requirements.md](02-requirements.md)
- [03-specification.md](03-specification.md)
- [04-design.md](04-design.md)
- [05-implementation.md](05-implementation.md)
- [decisions/](decisions/) — Architecture Decision Records

## How to engage

If you are picking this up cold, read STATUS.md first, then this README, then walk forward from the current phase. Each phase file's prompt section explains what that phase produces and how to know it's done.
