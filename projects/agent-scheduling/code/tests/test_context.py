"""Slice 1: AgentContext empty + JSON round-trip.

Entry point of phase 1 in 05-implementation.md. Currently fails at import —
agent_scheduling.context does not exist yet. Implementing AgentContext to
satisfy these two tests is the first TDD cycle.
"""
from pathlib import Path

from agent_scheduling.context import AgentContext


def test_empty_context_has_no_preferences():
    ctx = AgentContext.empty()
    assert ctx.preferences == {}


def test_context_round_trips_through_json(tmp_path: Path):
    ctx = AgentContext.empty()
    ctx.preferences["mornings"] = "preferred"
    path = tmp_path / "ctx.json"
    ctx.save(path)
    loaded = AgentContext.load(path)
    assert loaded.preferences == ctx.preferences
