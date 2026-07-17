"""Members — create/list/get (human aur agent, ek hi flat type)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from agent_deck.api.deps import RepoDep, member_or_404
from agent_deck.api.schemas import MemberCreate
from agent_deck.domain.models import Member

router = APIRouter(prefix="/members", tags=["members"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_member(body: MemberCreate, repo: RepoDep) -> Member:
    if repo.find_member_by_name(body.name) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"member already exists: {body.name}")
    return repo.add_member(
        Member(
            name=body.name,
            kind=body.kind,
            provider=body.provider,
            model=body.model,
            identity=body.identity,
        )
    )


@router.get("")
def list_members(repo: RepoDep) -> list[Member]:
    return repo.list_members()


@router.get("/{member_id}")
def get_member(member_id: str, repo: RepoDep) -> Member:
    return member_or_404(repo, member_id)
