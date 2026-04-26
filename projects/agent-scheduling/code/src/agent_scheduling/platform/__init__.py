"""Multi-tenant platform service: user management, groups, privacy, chat server.

See ../../04-design.md for the architecture. Slices 20+ build this out
incrementally; the entry point is `create_app()` in api.py.
"""
from agent_scheduling.platform.api import create_app

__all__ = ["create_app"]
