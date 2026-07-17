"""AgentRuntime — agent-members ke chalte-phirte LangGraph agents ka malik.

Ek agent-member ka runnable agent (model + identity + memory) EK baar banta hai,
phir reuse hota hai. API/CLI jaise callers ko bas ``reply_for(agent)`` chahiye —
LLM/provider wiring unki layer mein kabhi nahi aati (SRP).
"""

from __future__ import annotations

from dataclasses import dataclass

from agent_deck.config import Settings, build_model_for_member
from agent_deck.domain.models import Member
from agent_deck.runtime.chat import AgentReply, build_agent_reply


@dataclass(frozen=True)
class AgentContext:
    """Agent ke thread ka snapshot — context kitna bhara hai.
    Token counts pichhli LLM call ke ``usage_metadata`` se (input = current context)."""

    message_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class AgentRuntime:
    def __init__(self, settings: Settings, checkpointer) -> None:
        self._settings = settings
        self._checkpointer = checkpointer
        self._replies: dict[str, AgentReply] = {}  # agent.id -> built reply fn

    def reply_for(self, agent: Member) -> AgentReply:
        if agent.id not in self._replies:
            self._replies[agent.id] = build_agent_reply(
                build_model_for_member(agent, self._settings),
                system_prompt=agent.identity,
                checkpointer=self._checkpointer,
            )
        return self._replies[agent.id]

    def context_for(self, agent: Member) -> AgentContext:
        """Checkpoint se seedha padho — agent build kiye bina. Thread abhi tak
        nahi bana (kabhi baat nahi hui) to sab zero."""
        if agent.thread_id is None:
            return AgentContext()
        snapshot = self._checkpointer.get({"configurable": {"thread_id": agent.thread_id}})
        if snapshot is None:
            return AgentContext()
        messages = snapshot["channel_values"].get("messages", [])
        usage = next(
            (m.usage_metadata for m in reversed(messages) if m.type == "ai" and m.usage_metadata),
            None,
        )
        return AgentContext(
            message_count=len(messages),
            input_tokens=usage["input_tokens"] if usage else 0,
            output_tokens=usage["output_tokens"] if usage else 0,
            total_tokens=usage["total_tokens"] if usage else 0,
        )
