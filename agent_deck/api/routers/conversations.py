"""Conversations — DM containers aur unke visible messages."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from agent_deck.api.deps import RepoDep
from agent_deck.domain.models import Conversation, Message

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
def list_conversations(repo: RepoDep) -> list[Conversation]:
    return repo.list_conversations()


@router.get("/{conversation_id}/messages")
def list_messages(conversation_id: str, repo: RepoDep) -> list[Message]:
    if repo.get_conversation(conversation_id) is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"conversation not found: {conversation_id}"
        )
    return repo.list_messages(conversation_id)
