"""The domain records.

Each is a plain dataclass with a canonical ``id`` and JSON-portable fields.
Relations are by ``id`` only (no embedded documents, no driver references) so the
same records round-trip through any store unchanged. ``schema_version`` on the
stored entities carries future migrations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_deck.enums import (
    AgentProvider,
    MemberKind,
    MemberRole,
    SessionStatus,
)
from agent_deck.ids import new_id

SCHEMA_VERSION = 1


@dataclass
class Member:
    """A person or an agent — one base member type. ``manager_id`` points at the
    member that manages this one (None for a top-level manager)."""

    name: str
    kind: MemberKind
    role: MemberRole = MemberRole.MEMBER
    manager_id: str | None = None
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION

    @property
    def is_agent(self) -> bool:
        return self.kind is MemberKind.AGENT

    @property
    def is_manager(self) -> bool:
        return self.role is MemberRole.MANAGER


@dataclass
class Channel:
    """A team and its shared communication space — the same object.
    ``owner_id`` is the member (a manager) that owns the whole channel."""

    name: str
    owner_id: str
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION


@dataclass
class ChannelMembership:
    """A member's presence in a channel (a join record, by id)."""

    channel_id: str
    member_id: str
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION


@dataclass
class Ownership:
    """A manager owns an agent — the edge the permission engine reads to decide
    CONTROL_AGENT. Shallow by design: manager -> owned agent, one level."""

    manager_id: str
    agent_id: str
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION


@dataclass
class AgentConfig:
    """How one agent-member runs. Provider-agnostic: ``provider`` names the
    backend, ``model`` is that provider's model id."""

    member_id: str
    provider: AgentProvider = AgentProvider.CLAUDE
    model: str = "claude-opus-4-8"
    system_prompt: str = ""
    tool_names: list[str] = field(default_factory=list)
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION


@dataclass
class Message:
    """One post in a channel. ``created_at`` is an ISO-8601 string (JSON-portable);
    ``sequence_number`` is a channel-scoped monotonic counter for ordering."""

    channel_id: str
    from_member_id: str
    text: str
    created_at: str
    sequence_number: int
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION


@dataclass
class Session:
    """One agent working one objective. ``thread_id`` links this domain record to
    the LangGraph checkpoint that holds the agent's conversation memory."""

    channel_id: str
    agent_id: str
    thread_id: str
    objective: str
    status: SessionStatus = SessionStatus.PENDING
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION
