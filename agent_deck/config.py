"""Configuration — read the environment once, build the real chat model.

Nothing here needs to be set for tests (they inject stubs). For a real run,
provide a provider key (``ANTHROPIC_API_KEY`` or ``GOOGLE_API_KEY``) and
optionally ``MONGODB_URI``. Keys may also live in a ``.env`` file at the repo
root — it is loaded automatically (never overriding an already-set env var).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from agent_deck.enums import AgentProvider

DEFAULT_MODEL = "claude-opus-4-8"


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings."""

    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    mongodb_uri: str | None = None
    mongodb_db_name: str = "agent_deck"
    model: str = DEFAULT_MODEL


def load_dotenv(path: str = ".env") -> None:
    """Load ``KEY=value`` lines from a .env file into ``os.environ`` (only if not
    already set). No dependency; silently does nothing when the file is absent."""
    env_file = Path(path)
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_settings() -> Settings:
    """Build settings from environment (loading a .env first, if present)."""
    load_dotenv()
    return Settings(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        mongodb_uri=os.getenv("MONGODB_URI"),
        mongodb_db_name=os.getenv("AGENT_DECK_DB", "agent_deck"),
        model=os.getenv("AGENT_DECK_MODEL", DEFAULT_MODEL),
    )


def build_chat_model(settings: Settings | None = None):
    """Construct the default Claude chat model from settings (imports lazily)."""
    settings = settings or load_settings()
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model_name=settings.model,
        api_key=settings.anthropic_api_key,
    )


def build_model_for_member(member, settings: Settings | None = None):
    """Build the chat model an agent member runs on, routed by ``member.provider``.
    ``member.model`` picks the exact model id (e.g. a Gemini or Claude model)."""
    settings = settings or load_settings()

    if member.provider is AgentProvider.GEMINI:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=member.model,
            google_api_key=settings.google_api_key,
        )

    if member.provider is AgentProvider.CLAUDE:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model_name=member.model,
            api_key=settings.anthropic_api_key,
        )

    raise ValueError(f"provider not wired yet: {member.provider}")
