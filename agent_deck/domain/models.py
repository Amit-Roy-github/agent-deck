"""The domain records.

Each is a plain dataclass with a canonical ``id`` and JSON-portable fields.
Relations are by ``id`` only (no embedded documents, no driver references) so the
same records round-trip through any store unchanged. ``schema_version`` on the
stored entities carries future migrations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_deck.clock import now_iso
from agent_deck.enums import (
    AgentProvider,
    MemberKind,
    ReasoningEffort,
    SessionStatus,
    TrustLevel,
)
from agent_deck.ids import new_id

SCHEMA_VERSION = 1


@dataclass
class Member:
    """A person or an agent — one base, flat member type.

    There is no stored role: manager and member are the same entity, and being
    a "manager" is contextual (owning a channel), never a field here. Agent-run
    settings (provider/model/effort/trust/identity) live directly on the member,
    mirroring how Claude keeps a session — ``thread_id`` is our resumable handle
    (LangGraph's equivalent of Claude's session id).
    """

    name: str
    kind: MemberKind = MemberKind.AGENT
    color: str = ""
    provider: AgentProvider = AgentProvider.CLAUDE
    model: str = "claude-opus-4-8"
    effort: ReasoningEffort = ReasoningEffort.MEDIUM
    trust: TrustLevel = TrustLevel.SAFE
    identity: str = ""  # markdown: who this member is / its system prompt
    thread_id: str | None = None  # LangGraph checkpoint handle; None until first run
    created_at: str = field(default_factory=now_iso)
    last_active_at: str | None = None
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION

    @property
    def is_agent(self) -> bool:
        return self.kind is MemberKind.AGENT


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
