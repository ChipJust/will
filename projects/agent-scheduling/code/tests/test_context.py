"""Tests for AgentContext (slices 1 + 2)."""
from pathlib import Path

from agent_scheduling.context import AgentContext, ChatExchange


# Slice 1: empty + JSON round-trip


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


# Slice 2: update_from_chat (rule-based)


def test_update_from_chat_records_prefer_keyword():
    ctx = AgentContext.empty()
    exchanges = [ChatExchange(user_id="u1", text="I prefer mornings")]
    updated = ctx.update_from_chat(exchanges, user_id="u1")
    assert updated.preferences == {"mornings": "preferred"}


def test_update_from_chat_records_avoid_keyword():
    ctx = AgentContext.empty()
    exchanges = [ChatExchange(user_id="u1", text="please avoid mondays")]
    updated = ctx.update_from_chat(exchanges, user_id="u1")
    assert updated.preferences == {"mondays": "avoid"}


def test_update_from_chat_ignores_other_users():
    ctx = AgentContext.empty()
    exchanges = [
        ChatExchange(user_id="u2", text="I prefer afternoons"),
        ChatExchange(user_id="u1", text="I prefer mornings"),
    ]
    updated = ctx.update_from_chat(exchanges, user_id="u1")
    assert updated.preferences == {"mornings": "preferred"}


def test_update_from_chat_preserves_existing_preferences():
    ctx = AgentContext(preferences={"mondays": "avoid"})
    exchanges = [ChatExchange(user_id="u1", text="I prefer mornings")]
    updated = ctx.update_from_chat(exchanges, user_id="u1")
    assert updated.preferences == {"mondays": "avoid", "mornings": "preferred"}


def test_update_from_chat_does_not_mutate_original():
    ctx = AgentContext(preferences={"existing": "value"})
    exchanges = [ChatExchange(user_id="u1", text="I prefer mornings")]
    ctx.update_from_chat(exchanges, user_id="u1")
    assert ctx.preferences == {"existing": "value"}
