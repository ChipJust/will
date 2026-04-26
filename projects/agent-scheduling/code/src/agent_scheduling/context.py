"""Per-user preference context.

The agent reads this at the start of every negotiation and writes back to it
afterward (via post-mining or direct user input). One context per user; serialized
as JSON for portability between agent runs and across machines.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


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
