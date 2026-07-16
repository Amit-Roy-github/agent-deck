"""Permission-engine tests — the ownership model is the moat, so it is pinned
down here exhaustively: every (role x permission x relationship) that matters.

FROZEN: the permission layer is on hold while the member model is reshaped
(manager/member unified — role/manager_id dropped from Member). These tests use
the old Member shape and are skipped until the engine is refactored to derive
"manager" from channel ownership instead of a stored role.
"""

from __future__ import annotations

import pytest

from agent_deck.domain.models import Channel, Member, Ownership
from agent_deck.enums import MemberKind, MemberRole, Permission
from agent_deck.permissions import ROLE_CAPABILITIES, can

pytestmark = pytest.mark.skip(reason="permission layer frozen (member model reshape)")


def make_manager(name: str = "manager") -> Member:
    return Member(name=name, kind=MemberKind.HUMAN, role=MemberRole.MANAGER)


def make_agent(name: str = "agent", manager_id: str | None = None) -> Member:
    return Member(
        name=name,
        kind=MemberKind.AGENT,
        role=MemberRole.MEMBER,
        manager_id=manager_id,
    )


# --- SEND_MESSAGE : every member may post ---------------------------------


def test_every_role_may_send_message():
    manager = make_manager()
    agent = make_agent()
    assert can(manager, Permission.SEND_MESSAGE)
    assert can(agent, Permission.SEND_MESSAGE)


# --- CONTROL_SELF : only over oneself -------------------------------------


def test_member_controls_itself():
    agent = make_agent()
    assert can(agent, Permission.CONTROL_SELF, target=agent)


def test_member_cannot_control_another_member():
    agent = make_agent("a")
    other = make_agent("b")
    assert not can(agent, Permission.CONTROL_SELF, target=other)


# --- CONTROL_AGENT : manager over an agent it owns ------------------------


def test_manager_controls_owned_agent():
    manager = make_manager()
    agent = make_agent(manager_id=manager.id)
    edge = Ownership(owner_id=manager.id, agent_id=agent.id)
    assert can(manager, Permission.CONTROL_AGENT, target=agent, ownerships=[edge])


def test_manager_cannot_control_unowned_agent():
    manager = make_manager()
    foreign_agent = make_agent("foreign")
    assert not can(manager, Permission.CONTROL_AGENT, target=foreign_agent, ownerships=[])


def test_manager_controls_itself_as_agent_action():
    manager = make_manager()
    assert can(manager, Permission.CONTROL_AGENT, target=manager)


def test_plain_member_never_has_control_agent():
    agent = make_agent()
    owned = make_agent("owned")
    edge = Ownership(owner_id=agent.id, agent_id=owned.id)
    # Even with an ownership edge, a non-manager role lacks the capability.
    assert not can(agent, Permission.CONTROL_AGENT, target=owned, ownerships=[edge])


# --- CONTROL_CHANNEL : only the channel's owner-manager -------------------


def test_owner_manager_controls_channel():
    manager = make_manager()
    channel = Channel(name="research", owner_id=manager.id)
    assert can(manager, Permission.CONTROL_CHANNEL, channel=channel)


def test_manager_cannot_control_foreign_channel():
    manager = make_manager()
    other_channel = Channel(name="other", owner_id="someone-else")
    assert not can(manager, Permission.CONTROL_CHANNEL, channel=other_channel)


def test_member_cannot_control_channel_it_happens_to_own_field():
    # A member is never granted CONTROL_CHANNEL, even if owner_id matched.
    member = make_agent()
    channel = Channel(name="c", owner_id=member.id)
    assert not can(member, Permission.CONTROL_CHANNEL, channel=channel)


# --- Missing context denies by default ------------------------------------


def test_missing_context_denies():
    manager = make_manager()
    assert not can(manager, Permission.CONTROL_AGENT)  # no target
    assert not can(manager, Permission.CONTROL_CHANNEL)  # no channel
    assert not can(manager, Permission.CONTROL_SELF)  # no target


# --- Declarative contract stays the shape the engine relies on ------------


def test_role_capabilities_contract():
    assert ROLE_CAPABILITIES[MemberRole.MEMBER] == frozenset(
        {Permission.CONTROL_SELF, Permission.SEND_MESSAGE}
    )
    assert ROLE_CAPABILITIES[MemberRole.MANAGER] == frozenset(
        {
            Permission.CONTROL_CHANNEL,
            Permission.CONTROL_AGENT,
            Permission.CONTROL_SELF,
            Permission.SEND_MESSAGE,
        }
    )
