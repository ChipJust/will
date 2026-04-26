"""Per-user preference context.

The agent reads this at the start of every negotiation and writes back to it
afterward (via post-mining or direct user input). One context per user; serialized
as JSON for portability between agent runs and across machines.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ChatExchange:
    """A single chat post used as input to context mining."""
    user_id: str
    text: str


_PREFER_PATTERN = re.compile(r"\bprefer\s+(\w+)", re.IGNORECASE)
_AVOID_PATTERN = re.compile(r"\bavoid\s+(\w+)", re.IGNORECASE)


@dataclass
class AgentContext:
    preferences: dict = field(default_factory=dict)

    @classmethod
    def empty(cls) -> AgentContext:
        return cls()

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"preferences": self.preferences}))

    @classmethod
    def load(cls, path: Path) -> AgentContext:
        data = json.loads(path.read_text())
        return cls(preferences=data["preferences"])

    def update_from_chat(
        self, exchanges: list[ChatExchange], user_id: str
    ) -> AgentContext:
        """Return a new AgentContext with preferences extracted from this user's posts.

        Rule-based mining at this slice; LLM-driven mining is wired in later
        (see 05-implementation.md, post-negotiation mining slice).
        """
        new_prefs = dict(self.preferences)
        for exchange in exchanges:
            if exchange.user_id != user_id:
                continue
            for match in _PREFER_PATTERN.finditer(exchange.text):
                new_prefs[match.group(1).lower()] = "preferred"
            for match in _AVOID_PATTERN.finditer(exchange.text):
                new_prefs[match.group(1).lower()] = "avoid"
        return AgentContext(preferences=new_prefs)
