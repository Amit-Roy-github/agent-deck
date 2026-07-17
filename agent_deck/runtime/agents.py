"""AgentRuntime — agent-members ke chalte-phirte LangGraph agents ka malik.

Ek agent-member ka runnable agent (model + identity + memory) EK baar banta hai,
phir reuse hota hai. API/CLI jaise callers ko bas ``reply_for(agent)`` chahiye —
LLM/provider wiring unki layer mein kabhi nahi aati (SRP).
"""

from __future__ import annotations

from agent_deck.config import Settings, build_model_for_member
from agent_deck.domain.models import Member
from agent_deck.runtime.chat import AgentReply, build_agent_reply


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
