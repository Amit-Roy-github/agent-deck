"""Sessions — agent runs (lifecycle ke saath), read-only view."""

from __future__ import annotations

from fastapi import APIRouter

from agent_deck.api.deps import RepoDep
from agent_deck.domain.models import Session

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
def list_sessions(repo: RepoDep) -> list[Session]:
    return repo.list_sessions()
