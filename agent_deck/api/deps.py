"""API dependencies — routers yahan se apni zaroorat ki cheezein lete hain (DI).

``create_app`` repo/runtime ko ``app.state`` par rakhta hai; ye getters unhe
FastAPI ``Depends`` ke through routers tak pahunchate hain. Router kabhi khud
store/LLM nahi banata — sirf maangta hai (dependency inversion).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from agent_deck.domain.models import Member
from agent_deck.runtime.agents import AgentRuntime
from agent_deck.store import Repository


def get_repo(request: Request) -> Repository:
    return request.app.state.repo


def get_agent_runtime(request: Request) -> AgentRuntime:
    return request.app.state.agent_runtime


RepoDep = Annotated[Repository, Depends(get_repo)]
AgentRuntimeDep = Annotated[AgentRuntime, Depends(get_agent_runtime)]


def member_or_404(repo: Repository, member_id: str) -> Member:
    member = repo.get_member(member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"member not found: {member_id}")
    return member
