"""Chat — ek turn: member apne agent ko text bhejta, agent reply karta.

Router thin hai: validate + delegate. Asli kaam ``runtime/chat.send_message``
mein hota hai (message store, session lifecycle, agent run)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from agent_deck.api.deps import AgentRuntimeDep, RepoDep, member_or_404
from agent_deck.api.schemas import (
    ChatPreviewRequest,
    ChatPreviewResult,
    ChatRequest,
    ChatResult,
)
from agent_deck.runtime.chat import send_message

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(body: ChatRequest, repo: RepoDep, agent_runtime: AgentRuntimeDep) -> ChatResult:
    sender = member_or_404(repo, body.sender_id)
    agent = member_or_404(repo, body.agent_id)
    if not agent.is_agent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "target member is not an agent")
    if not repo.owns(sender.id, agent.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "sender does not own this agent")
    conversation, session, message = send_message(
        repo, agent_runtime.reply_for(agent), owner=sender, agent=agent, text=body.text
    )
    return ChatResult(
        conversation_id=conversation.id,
        session_id=session.id,
        reply=message,
    )


@router.post("/chat/preview")
def chat_preview(body: ChatPreviewRequest, agent_runtime: AgentRuntimeDep) -> ChatPreviewResult:
    """Test-drive an unsaved agent config — one stateless reply, nothing stored.
    No sender/ownership needed since no member or conversation is created."""
    reply = agent_runtime.preview_reply(
        provider=body.provider,
        model=body.model,
        effort=body.effort,
        identity=body.identity,
        text=body.text,
    )
    return ChatPreviewResult(reply=reply)
