"""The permission engine — the single source of truth for "who may do what".

Two layers, both explicit:

1. ROLE_CAPABILITIES — a declarative map (role -> the capabilities it can ever
   hold). This is the contract; read it and you know the whole model.
2. can(...) — refines that baseline with the *relationship* between actor and
   target: a manager may CONTROL_AGENT only over an agent it actually owns, and
   CONTROL_CHANNEL only over a channel it actually owns.

Pure and store-independent: it reads records you pass in, touches no database,
and is fully unit-testable.
"""

from __future__ import annotations

from collections.abc import Iterable

from agent_deck.domain.models import Channel, Member, Ownership
from agent_deck.enums import MemberRole, Permission

# Layer 1 — what each role can ever hold (declarative contract).
ROLE_CAPABILITIES: dict[MemberRole, frozenset[Permission]] = {
    MemberRole.MANAGER: frozenset(
        {
            Permission.CONTROL_CHANNEL,
            Permission.CONTROL_AGENT,
            Permission.CONTROL_SELF,
            Permission.SEND_MESSAGE,
        }
    ),
    MemberRole.MEMBER: frozenset(
        {
            Permission.CONTROL_SELF,
            Permission.SEND_MESSAGE,
        }
    ),
}


def can(
    actor: Member,
    action: Permission,
    *,
    target: Member | None = None,
    channel: Channel | None = None,
    ownerships: Iterable[Ownership] = (),
) -> bool:
    """Return whether ``actor`` may perform ``action``.

    ``target``/``channel`` are the thing acted upon; ``ownerships`` are the
    manager->agent edges consulted for CONTROL_AGENT. Missing context that an
    action needs yields False (deny by default) rather than raising.
    """
    if action not in ROLE_CAPABILITIES[actor.role]:
        return False

    if action is Permission.SEND_MESSAGE:
        return True

    if action is Permission.CONTROL_SELF:
        return target is not None and target.id == actor.id

    if action is Permission.CONTROL_AGENT:
        if target is None:
            return False
        if target.id == actor.id:
            return True  # controlling oneself is always allowed
        return any(
            edge.owner_id == actor.id and edge.agent_id == target.id
            for edge in ownerships
        )

    if action is Permission.CONTROL_CHANNEL:
        return channel is not None and channel.owner_id == actor.id

    return False
