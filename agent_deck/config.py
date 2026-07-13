"""Configuration — read the environment once, build the real chat model.

Nothing here needs to be set for tests (they inject stubs). For a real run,
provide ``ANTHROPIC_API_KEY`` and optionally ``MONGODB_URI``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MODEL = "claude-opus-4-8"


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings."""

    anthropic_api_key: str | None = None
    mongodb_uri: str | None = None
    mongodb_db_name: str = "agent_deck"
    model: str = DEFAULT_MODEL


def load_settings() -> Settings:
    """Build settings from environment variables."""
    return Settings(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        mongodb_uri=os.getenv("MONGODB_URI"),
        mongodb_db_name=os.getenv("AGENT_DECK_DB", "agent_deck"),
        model=os.getenv("AGENT_DECK_MODEL", DEFAULT_MODEL),
    )


def build_chat_model(settings: Settings | None = None):
    """Construct the Claude chat model from settings (imports lazily)."""
    settings = settings or load_settings()
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model_name=settings.model,
        api_key=settings.anthropic_api_key,
    )
