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

from agent_deck.enums import AgentProvider, ReasoningEffort

DEFAULT_MODEL = "claude-opus-4-8"
# chat ke liye default Gemini: lite = ~1s reply (gemini-3.5-flash ~40s thinking karta)
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_DB_NAME = "agent_deck"

# auto-compact: context itne tokens paar kare to purani history summary ban jati
# hai (last N messages as-is rehte). Values checkpoint mein hi update hoti hai.
SUMMARY_TRIGGER_TOKENS = 6000
SUMMARY_KEEP_MESSAGES = 20

# Gemini ka thinking_level sirf minimal|low|medium|high leta hai (verified) —
# humare upar ke efforts wahan clamp hote hai. Claude effort humare enum values
# seedha leta hai (low|medium|high|xhigh|max — verified), mapping ki zaroorat nahi.
_GEMINI_THINKING: dict[ReasoningEffort, str] = {
    ReasoningEffort.LOW: "low",
    ReasoningEffort.MEDIUM: "medium",
    ReasoningEffort.HIGH: "high",
    ReasoningEffort.XHIGH: "high",
    ReasoningEffort.MAX: "high",
}


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings."""

    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    mongodb_uri: str | None = None
    mongodb_db_name: str = DEFAULT_DB_NAME
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
        mongodb_db_name=os.getenv("AGENT_DECK_DB", DEFAULT_DB_NAME),
        model=os.getenv("AGENT_DECK_MODEL", DEFAULT_MODEL),
    )


def _chat_model(
    provider: AgentProvider,
    model_name: str,
    settings: Settings,
    effort: ReasoningEffort | None = None,
):
    """Provider -> chat model construction, EK jagah (imports lazily).
    ``effort`` = kitna sochna hai — provider apne param mein leta hai."""
    if provider is AgentProvider.GEMINI:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.google_api_key,
            thinking_level=_GEMINI_THINKING[effort] if effort else None,
        )

    if provider is AgentProvider.CLAUDE:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model_name=model_name,
            api_key=settings.anthropic_api_key,
            effort=effort.value if effort else None,
        )

    raise ValueError(f"provider not wired yet: {provider}")


def build_chat_model(settings: Settings | None = None):
    """Construct the default Claude chat model from settings."""
    settings = settings or load_settings()
    return _chat_model(AgentProvider.CLAUDE, settings.model, settings)


def build_model_for_member(member, settings: Settings | None = None):
    """Build the chat model an agent member runs on, routed by ``member.provider``.
    ``member.model`` picks the exact model id; ``member.effort`` routes thinking."""
    settings = settings or load_settings()
    return _chat_model(member.provider, member.model, settings, effort=member.effort)
