"""Member model — the reshaped, flat member (no role, no manager_id)."""

from __future__ import annotations

from agent_deck.domain.models import Member
from agent_deck.enums import AgentProvider, MemberKind, ReasoningEffort, TrustLevel


def test_member_defaults_are_a_claude_agent():
    member = Member(name="Researcher")
    assert member.kind is MemberKind.AGENT
    assert member.provider is AgentProvider.CLAUDE
    assert member.model == "claude-opus-4-8"
    assert member.effort is ReasoningEffort.MEDIUM
    assert member.trust is TrustLevel.SAFE
    assert member.thread_id is None  # no session yet
    assert member.last_active_at is None


def test_member_gets_a_canonical_id_and_timestamp():
    a = Member(name="A")
    b = Member(name="B")
    assert a.id and b.id and a.id != b.id  # unique app-generated ids
    assert a.created_at.endswith("+00:00")  # ISO-8601 UTC


def test_member_has_no_role_or_manager_id():
    member = Member(name="Flat")
    # manager and member are the same entity — these fields must not exist.
    assert not hasattr(member, "role")
    assert not hasattr(member, "manager_id")


def test_thread_id_is_the_resumable_session_handle():
    member = Member(name="Resumable", thread_id="thread-123")
    assert member.thread_id == "thread-123"
