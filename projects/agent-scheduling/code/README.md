# agent-scheduling — code

Python package skeleton for the agent-scheduling project. See `../05-implementation.md` for the slice-by-slice TDD plan, `../04-design.md` for the architecture and code layout, and `../03-specification.md` for the contract.

## Quickstart

```bash
uv sync
uv run pytest
```

The first test fails by design — slice 1 of `../05-implementation.md` drives out the implementation that makes it pass.

## Layout

```
src/agent_scheduling/
└── __init__.py
tests/
├── __init__.py
└── test_context.py
```

Modules from `04-design.md` (`context.py`, `adapters/`, `protocol.py`, …) get added as TDD slices drive them out. Do not stub them ahead of time.
