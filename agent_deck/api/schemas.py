"""API request/response contracts. Requests are Pydantic models; responses are
the domain dataclasses themselves (FastAPI serializes them directly, so the wire
shape IS the domain shape) — composite responses like ``ChatResult`` are also
dataclasses over domain records."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from agent_deck.config import DEFAULT_GEMINI_MODEL
from agent_deck.domain.models import Message
from agent_deck.enums import AgentProvider, MemberKind, ReasoningEffort


class MemberCreate(BaseModel):
    """Create a human or an agent member."""

    name: str = Field(min_length=1)
    kind: MemberKind = MemberKind.HUMAN
    # agent-only settings (ignored for humans)
    provider: AgentProvider = AgentProvider.GEMINI
    model: str = DEFAULT_GEMINI_MODEL
    effort: ReasoningEffort = ReasoningEffort.MEDIUM
    identity: str = ""


class OwnershipCreate(BaseModel):
    """owner (member) -> owned agent."""

    owner_id: str
    agent_id: str


class ChatRequest(BaseModel):
    """One chat turn: a member sends text to an agent they own."""

    sender_id: str
    agent_id: str
    text: str = Field(min_length=1)


class ChatPreviewRequest(BaseModel):
    """Test-drive an unsaved agent config: reply once, persist nothing.
    No member/session/memory is created — a stateless one-shot for the create UI."""

    provider: AgentProvider = AgentProvider.CLAUDE
    model: str = Field(min_length=1)
    effort: ReasoningEffort = ReasoningEffort.MEDIUM
    identity: str = ""
    text: str = Field(min_length=1)


@dataclass
class ChatResult:
    """One chat turn ka result — kis DM mein, kaunsa run, aur agent ka reply."""

    conversation_id: str
    session_id: str
    reply: Message


@dataclass
class ChatPreviewResult:
    """A test-drive reply — just the agent's text, nothing stored."""

    reply: str
