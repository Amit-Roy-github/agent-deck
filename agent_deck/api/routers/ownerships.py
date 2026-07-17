"""Ownerships — owner (member) -> owned agent ka edge."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from agent_deck.api.deps import RepoDep, member_or_404
from agent_deck.api.schemas import OwnershipCreate
from agent_deck.domain.models import Ownership

router = APIRouter(prefix="/ownerships", tags=["ownerships"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_ownership(body: OwnershipCreate, repo: RepoDep) -> Ownership:
    owner = member_or_404(repo, body.owner_id)
    agent = member_or_404(repo, body.agent_id)
    if not agent.is_agent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "owned member must be an agent")
    if repo.owns(owner.id, agent.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "ownership already exists")
    return repo.add_ownership(Ownership(owner_id=owner.id, agent_id=agent.id))


@router.get("")
def list_ownerships(repo: RepoDep) -> list[Ownership]:
    return repo.list_ownerships()
