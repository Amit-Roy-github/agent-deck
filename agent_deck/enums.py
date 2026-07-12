"""Canonical enums — the vocabulary of the domain.

No string literals anywhere else in the codebase; every categorical value
lives here so a reader (human or AI) learns the whole vocabulary in one place.
Values are plain lowercase strings so records stay JSON-portable across stores.
"""

from __future__ import annotations

from enum import Enum


class MemberKind(str, Enum):
    """A member is either a person or an AI agent — one base member type."""

    HUMAN = "human"
    AGENT = "agent"


class MemberRole(str, Enum):
    """A member's role inside a channel. The manager runs the channel; the
    manager may itself be a HUMAN or an AGENT (interchangeable)."""

    MANAGER = "manager"
    MEMBER = "member"


class Permission(str, Enum):
    """The four first-class capabilities — the ownership model, our moat.

    - CONTROL_SELF    : act on oneself (every member has this).
    - CONTROL_AGENT   : act on an agent one owns (managers, over owned agents).
    - CONTROL_CHANNEL : act on the whole channel (the channel's owner-manager).
    - SEND_MESSAGE    : post in the channel (every member has this).
    """

    CONTROL_SELF = "control_self"
    CONTROL_AGENT = "control_agent"
    CONTROL_CHANNEL = "control_channel"
    SEND_MESSAGE = "send_message"


class SessionStatus(str, Enum):
    """Lifecycle of one agent session (an objective being worked)."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentProvider(str, Enum):
    """The backend an agent runs on. Provider-agnostic by design — the schema
    accommodates non-Claude backends; default is Claude. Extensible."""

    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
