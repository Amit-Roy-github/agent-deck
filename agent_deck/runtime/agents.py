"""AgentRuntime — agent-members ke chalte-phirte LangGraph agents ka malik.

Ek agent-member ka runnable agent (model + identity + memory) EK baar banta hai,
phir reuse hota hai. API/CLI jaise callers ko bas ``reply_for(agent)`` chahiye —
LLM/provider wiring unki layer mein kabhi nahi aati (SRP).
"""

from __future__ import annotations

from dataclasses import dataclass

from agent_deck.config import MANUAL_COMPACT_KEEP_MESSAGES, Settings, build_model_for_member
from agent_deck.domain.models import Member
from agent_deck.runtime.chat import AgentReply, build_agent, reply_from


@dataclass(frozen=True)
class AgentContext:
    """Agent ke thread ka snapshot — context kitna bhara hai.
    Token counts pichhli LLM call ke ``usage_metadata`` se (input = current context)."""

    message_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class CompactResult:
    """Manual compact ka result — pehle/baad ka context snapshot."""

    compacted: bool
    before: AgentContext
    after: AgentContext


class AgentRuntime:
    def __init__(self, settings: Settings, checkpointer) -> None:
        self._settings = settings
        self._checkpointer = checkpointer
        self._graphs: dict[str, object] = {}  # agent.id -> built LangGraph agent

    def _graph_for(self, agent: Member):
        if agent.id not in self._graphs:
            self._graphs[agent.id] = build_agent(
                build_model_for_member(agent, self._settings),
                system_prompt=agent.identity,
                checkpointer=self._checkpointer,
            )
        return self._graphs[agent.id]

    def reply_for(self, agent: Member) -> AgentReply:
        return reply_from(self._graph_for(agent))

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

    def compact_for(self, agent: Member) -> CompactResult:
        """Manual compact — ABHI: last ``MANUAL_COMPACT_KEEP_MESSAGES`` ke alawa
        poori history ek summary message ban jati hai, checkpoint mein hi (auto-compact
        wahi karta hai, bas token-threshold pe; yahan user ke bole pe force)."""
        from langchain.agents.middleware import SummarizationMiddleware

        before = self.context_for(agent)
        if agent.thread_id is None or before.message_count <= MANUAL_COMPACT_KEEP_MESSAGES:
            return CompactResult(compacted=False, before=before, after=before)

        graph = self._graph_for(agent)
        config = {"configurable": {"thread_id": agent.thread_id}}
        messages = graph.get_state(config).values.get("messages", [])
        # wahi middleware, bas trigger = "itne messages hai to chalao" (force)
        summarizer = SummarizationMiddleware(
            build_model_for_member(agent, self._settings),
            trigger=("messages", MANUAL_COMPACT_KEEP_MESSAGES + 1),
            keep=("messages", MANUAL_COMPACT_KEEP_MESSAGES),
        )
        update = summarizer.before_model({"messages": messages}, None)
        if update is None:
            return CompactResult(compacted=False, before=before, after=before)
        graph.update_state(config, update)
        return CompactResult(compacted=True, before=before, after=self.context_for(agent))
