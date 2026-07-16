"""Repository — the one interface the app uses to read/write domain records.

Keeps orchestration code free of any store detail. ``InMemoryRepository`` holds
everything in dicts/lists (keyless, fast, test-friendly). A Mongo-backed class
will implement the same ``Repository`` protocol later — callers won't change.

Three record families live here:
- **Conversation** : the 1:1 chat container (DM).
- **Session**      : one agent run (a bounded execution with a lifecycle).
- **Message**      : one visible chat turn, scoped to a conversation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agent_deck.domain.models import Conversation, Member, Message, Ownership, Session


@runtime_checkable
class Repository(Protocol):
    """Storage contract. Relations are by id only (see domain models)."""

    # --- members ---
    def add_member(self, member: Member) -> Member: ...
    def get_member(self, member_id: str) -> Member | None: ...
    def list_members(self) -> list[Member]: ...

    # --- ownerships (owner member -> owned agent) ---
    def add_ownership(self, ownership: Ownership) -> Ownership: ...
    def list_ownerships(self) -> list[Ownership]: ...
    def owns(self, owner_id: str, agent_id: str) -> bool: ...

    # --- conversations (1:1 chat container) ---
    def add_conversation(self, conversation: Conversation) -> Conversation: ...
    def get_conversation(self, conversation_id: str) -> Conversation | None: ...
    def find_direct_conversation(self, member_a_id: str, member_b_id: str) -> Conversation | None: ...
    def list_conversations(self) -> list[Conversation]: ...

    # --- sessions (one agent run) ---
    def add_session(self, session: Session) -> Session: ...
    def get_session(self, session_id: str) -> Session | None: ...
    def update_session(self, session: Session) -> Session: ...
    def list_sessions(self) -> list[Session]: ...

    # --- messages (visible chat turns, scoped by conversation_id here) ---
    def add_message(self, message: Message) -> Message: ...
    def list_messages(self, conversation_id: str) -> list[Message]: ...


class InMemoryRepository:
    """Keyless in-memory store. Same interface a Mongo repo will implement."""

    def __init__(self) -> None:
        self._members: dict[str, Member] = {}
        self._ownerships: list[Ownership] = []
        self._conversations: dict[str, Conversation] = {}
        self._sessions: dict[str, Session] = {}
        self._messages: list[Message] = []  # append-only, ordered by insertion

    # --- members ---
    def add_member(self, member: Member) -> Member:
        self._members[member.id] = member
        return member

    def get_member(self, member_id: str) -> Member | None:
        return self._members.get(member_id)

    def list_members(self) -> list[Member]:
        return list(self._members.values())

    # --- ownerships ---
    def add_ownership(self, ownership: Ownership) -> Ownership:
        self._ownerships.append(ownership)
        return ownership

    def list_ownerships(self) -> list[Ownership]:
        return list(self._ownerships)

    def owns(self, owner_id: str, agent_id: str) -> bool:
        return any(
            o.owner_id == owner_id and o.agent_id == agent_id
            for o in self._ownerships
        )

    # --- conversations ---
    def add_conversation(self, conversation: Conversation) -> Conversation:
        self._conversations[conversation.id] = conversation
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self._conversations.get(conversation_id)

    def find_direct_conversation(
        self, member_a_id: str, member_b_id: str
    ) -> Conversation | None:
        pair = {member_a_id, member_b_id}  # order-agnostic
        for conversation in self._conversations.values():
            if {conversation.member_a_id, conversation.member_b_id} == pair:
                return conversation
        return None

    def list_conversations(self) -> list[Conversation]:
        return list(self._conversations.values())

    # --- sessions ---
    def add_session(self, session: Session) -> Session:
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def update_session(self, session: Session) -> Session:
        self._sessions[session.id] = session
        return session

    def list_sessions(self) -> list[Session]:
        return list(self._sessions.values())

    # --- messages ---
    def add_message(self, message: Message) -> Message:
        # per-conversation monotonic ordering, assigned by the store
        message.sequence_number = sum(
            1 for m in self._messages if m.conversation_id == message.conversation_id
        )
        self._messages.append(message)
        return message

    def list_messages(self, conversation_id: str) -> list[Message]:
        return sorted(
            (m for m in self._messages if m.conversation_id == conversation_id),
            key=lambda m: m.sequence_number,
        )
