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
    thread_id: str | None = None  # the agent's ONE LangGraph memory (all its chats
    # share it for now; per-conversation / per-channel threads come later). None
    # until first run, then assigned once and reused.
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
    ``owner_id`` is the member that owns the whole channel; ``description`` is the
    channel's "about" — what this team is for."""

    name: str
    owner_id: str
    description: str = ""
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
    """A member owns an agent — the edge the permission engine reads to decide
    CONTROL_AGENT. ``owner_id`` is just a member (no "manager" is stored anywhere);
    "manager" is a derived label = owns a channel or holds an ownership edge.
    Shallow by design: owner -> owned agent, one level."""

    owner_id: str
    agent_id: str
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION


@dataclass
class Conversation:
    """A direct 1:1 chat between two members — the DM container.
    Handles every 1:1 axis: human<->agent, human<->human, agent<->agent. Holds the
    visible messages; ``thread_id`` is the agent's memory handle — for now it is the
    agent's ONE thread (``Member.thread_id``), so every chat shares it. Long-lived:
    it accumulates, it has NO run lifecycle (that's a Session)."""

    member_a_id: str
    member_b_id: str
    thread_id: str | None = None
    created_at: str = field(default_factory=now_iso)
    last_message_at: str | None = None
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION


@dataclass
class Message:
    """One visible chat turn. Belongs to a ``conversation_id`` (1:1) or a
    ``channel_id`` (group) — one is set. ``sequence_number`` is a per-container
    monotonic counter set by the store; ``created_at`` is ISO-8601 UTC."""

    from_member_id: str
    text: str
    conversation_id: str | None = None
    channel_id: str | None = None
    sequence_number: int = 0
    created_at: str = field(default_factory=now_iso)
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION


@dataclass
class Session:
    """One agent RUN — a bounded execution episode with a lifecycle, SEPARATE from
    the chat turns. It runs on ``thread_id`` inside a ``conversation_id`` (or a
    ``channel_id`` later), on an ``objective``, moving PENDING -> RUNNING ->
    COMPLETED/FAILED. Many sessions can occur over one conversation's life."""

    agent_id: str
    thread_id: str
    conversation_id: str | None = None
    channel_id: str | None = None
    objective: str = ""
    status: SessionStatus = SessionStatus.PENDING
    created_at: str = field(default_factory=now_iso)
    completed_at: str | None = None
    id: str = field(default_factory=new_id)
    schema_version: int = SCHEMA_VERSION
