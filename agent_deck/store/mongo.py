"""MongoDB-backed Repository — same protocol as ``InMemoryRepository``.

One collection per record family; the record's canonical ``id`` is stored as
Mongo's ``_id`` (no ObjectId anywhere). Enums are written as their plain string
values and coerced back on read, so a document round-trips to the exact same
dataclass — the domain stays JSON-portable, as promised in ``domain/models.py``.
"""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import get_args, get_type_hints

from pymongo import ASCENDING, MongoClient

from agent_deck.domain.models import Conversation, Member, Message, Ownership, Session
from agent_deck.enums import Collection

_HINTS_CACHE: dict[type, dict] = {}


def to_doc(record) -> dict:
    """Dataclass -> Mongo document: enums to values, ``id`` becomes ``_id``."""
    doc = {
        key: (value.value if isinstance(value, Enum) else value)
        for key, value in asdict(record).items()
    }
    doc["_id"] = doc.pop("id")
    return doc


def _enum_in(hint) -> type[Enum] | None:
    """Hint mein enum class dhundo — seedha (``MemberKind``) ya union ke andar
    (``AgentProvider | None``). Nahi mila to None."""
    if isinstance(hint, type) and issubclass(hint, Enum):
        return hint
    for arg in get_args(hint):
        if isinstance(arg, type) and issubclass(arg, Enum):
            return arg
    return None


def from_doc(cls, doc: dict):
    """Mongo document -> dataclass: ``_id`` back to ``id``, strings to enums.
    Unknown keys are dropped (forward-compat with future schema versions)."""
    hints = _HINTS_CACHE.setdefault(cls, get_type_hints(cls))
    data = {}
    for key, value in doc.items():
        if key == "_id":
            data["id"] = value
            continue
        if key not in hints:
            continue  # field this code version doesn't know
        enum_cls = _enum_in(hints[key])
        if enum_cls is not None and value is not None:
            value = enum_cls(value)
        data[key] = value
    return cls(**data)


class MongoRepository:
    """Mongo implementation of the ``Repository`` protocol."""

    def __init__(self, client: MongoClient, db_name: str = "agent_deck") -> None:
        db = client[db_name]
        self._members = db[Collection.MEMBERS.value]
        self._ownerships = db[Collection.OWNERSHIPS.value]
        self._conversations = db[Collection.CONVERSATIONS.value]
        self._sessions = db[Collection.SESSIONS.value]
        self._messages = db[Collection.MESSAGES.value]
        # idempotent — cheap to call on every startup
        self._messages.create_index(
            [("conversation_id", ASCENDING), ("sequence_number", ASCENDING)]
        )

    # --- members ---
    def add_member(self, member: Member) -> Member:
        # upsert: also persists in-place updates (e.g. an assigned thread_id)
        self._members.replace_one({"_id": member.id}, to_doc(member), upsert=True)
        return member

    def get_member(self, member_id: str) -> Member | None:
        doc = self._members.find_one({"_id": member_id})
        return from_doc(Member, doc) if doc else None

    def find_member_by_name(self, name: str) -> Member | None:
        doc = self._members.find_one({"name": name})
        return from_doc(Member, doc) if doc else None

    def list_members(self) -> list[Member]:
        return [from_doc(Member, doc) for doc in self._members.find()]

    # --- ownerships ---
    def add_ownership(self, ownership: Ownership) -> Ownership:
        self._ownerships.replace_one({"_id": ownership.id}, to_doc(ownership), upsert=True)
        return ownership

    def list_ownerships(self) -> list[Ownership]:
        return [from_doc(Ownership, doc) for doc in self._ownerships.find()]

    def owns(self, owner_id: str, agent_id: str) -> bool:
        return (
            self._ownerships.count_documents(
                {"owner_id": owner_id, "agent_id": agent_id}, limit=1
            )
            > 0
        )

    # --- conversations ---
    def add_conversation(self, conversation: Conversation) -> Conversation:
        self._conversations.replace_one(
            {"_id": conversation.id}, to_doc(conversation), upsert=True
        )
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        doc = self._conversations.find_one({"_id": conversation_id})
        return from_doc(Conversation, doc) if doc else None

    def find_direct_conversation(
        self, member_a_id: str, member_b_id: str
    ) -> Conversation | None:
        doc = self._conversations.find_one(
            {
                "$or": [  # order-agnostic, same as InMemoryRepository
                    {"member_a_id": member_a_id, "member_b_id": member_b_id},
                    {"member_a_id": member_b_id, "member_b_id": member_a_id},
                ]
            }
        )
        return from_doc(Conversation, doc) if doc else None

    def list_conversations(self) -> list[Conversation]:
        return [from_doc(Conversation, doc) for doc in self._conversations.find()]

    # --- sessions ---
    def add_session(self, session: Session) -> Session:
        self._sessions.replace_one({"_id": session.id}, to_doc(session), upsert=True)
        return session

    def get_session(self, session_id: str) -> Session | None:
        doc = self._sessions.find_one({"_id": session_id})
        return from_doc(Session, doc) if doc else None

    def update_session(self, session: Session) -> Session:
        return self.add_session(session)

    def list_sessions(self) -> list[Session]:
        return [from_doc(Session, doc) for doc in self._sessions.find()]

    # --- messages ---
    def add_message(self, message: Message) -> Message:
        # per-conversation monotonic ordering, assigned by the store
        message.sequence_number = self._messages.count_documents(
            {"conversation_id": message.conversation_id}
        )
        self._messages.insert_one(to_doc(message))
        return message

    def list_messages(self, conversation_id: str) -> list[Message]:
        cursor = self._messages.find({"conversation_id": conversation_id}).sort(
            "sequence_number", ASCENDING
        )
        return [from_doc(Message, doc) for doc in cursor]
