# agent-scheduling — code

Python package for the agent-scheduling project. See `../05-implementation.md` for the slice-by-slice TDD plan, `../04-design.md` for the architecture, and `../03-specification.md` for the contract.

## Quickstart

```bash
uv sync
uv run pytest
```

## Status (as of 2026-04-26)

Phases 1–3 complete. 135 tests passing. See `../STATUS.md` for the full state.

## Layout

```
src/agent_scheduling/
├── __init__.py
├── context.py       # AgentContext load/save/update
├── adapters/        # Pluggable email/calendar adapters
│   ├── base.py      # Protocol + value types
│   └── mock.py      # MockAdapter for tests
├── pattern.py       # MeetingPattern (cohort rhythm)
├── privacy.py       # Directional per-edge privacy filter
├── protocol.py      # Envelope + MessageType enum
├── solver.py        # Batch CSP + assign_sources + analyze_deadlock + apply_relaxations
├── negotiator.py    # State machine for the agent-to-agent protocol
└── platform/        # Multi-tenant platform service
    ├── api.py       # FastAPI app + WebSocket
    └── chat.py      # ChatRoom + RoomRegistry + SqliteChatStore
tests/
├── test_*.py        # One file per module above
```
