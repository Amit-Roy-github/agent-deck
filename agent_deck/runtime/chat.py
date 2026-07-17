"""Direct chat runtime — a member talks to an agent, everything stored, cleanly
split into the two concepts:

- **Conversation** : the 1:1 chat container (Slack-DM-like). Created once.
- **Session**      : one agent RUN per reply (PENDING->RUNNING->COMPLETED/FAILED).
- **Message**      : each visible turn (human text + agent's final text).

One turn:
  member sends text
    -> get-or-create the Conversation (thread_id = agent's memory key)
    -> store the member's Message
    -> open a Session (run) for the agent
    -> agent replies (LangGraph, memory via thread_id)   [Session RUNNING]
    -> store the agent's Message                          [Session COMPLETED]

The reply step is injected as an ``AgentReply`` callable, so this module never
imports LangGraph — it stays about *storage + orchestration* and is testable with
a stub. (Same dependency-inversion idea as ``Researcher``.)
"""

from __future__ import annotations

from typing import Callable

from agent_deck.clock import now_iso
from agent_deck.domain.models import Conversation, Member, Message, Session
from agent_deck.ids import new_id
from agent_deck.runtime.lifecycle import session_run
from agent_deck.store.repository import Repository

# (thread_id, user_text) -> reply_text. Decouples chat from any LLM/provider.
AgentReply = Callable[[str, str], str]

DEFAULT_SYSTEM_PROMPT = "Tum ek madadgar assistant ho. Chhota, seedha jawab do."
CHAT_OBJECTIVE = "chat reply"


def message_text(content: object) -> str:
    """Pull plain text from a reply. Gemini 3.x / Claude return a LIST of content
    blocks ([{'type':'text','text':...}, ...]); older models a plain str. Both ok."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)


def build_agent_reply(model, *, system_prompt: str = "", checkpointer=None) -> AgentReply:
    """Wrap a chat model into an ``AgentReply``: a plain conversational agent
    (no tools, no structured output) whose memory lives in ``checkpointer``."""
    from langchain.agents import create_agent

    agent = create_agent(
        model,
        tools=[],
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    def reply(thread_id: str, user_text: str) -> str:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_text}]},
            config={"configurable": {"thread_id": thread_id}},
        )
        return message_text(result["messages"][-1].content)

    return reply


def ensure_agent_thread(repo: Repository, agent: Member) -> str:
    """The agent's ONE memory thread. Assigned once on first use, then reused for
    every chat (per-conversation / per-channel threads come later). Persisted back."""
    if agent.thread_id is None:
        agent.thread_id = new_id()
        repo.add_member(agent)  # persist the assigned thread
    return agent.thread_id


def get_or_create_direct_conversation(
    repo: Repository, member_a: Member, member_b: Member, thread_id: str
) -> Conversation:
    """The single 1:1 chat between these two members (order-agnostic). Runs on the
    agent's ``thread_id`` (one thread per agent for now)."""
    existing = repo.find_direct_conversation(member_a.id, member_b.id)
    if existing is not None:
        return existing
    conversation = Conversation(
        member_a_id=member_a.id,
        member_b_id=member_b.id,
        thread_id=thread_id,  # = the agent's single thread
    )
    return repo.add_conversation(conversation)


def send_message(
    repo: Repository,
    reply: AgentReply,
    *,
    owner: Member,
    agent: Member,
    text: str,
) -> tuple[Conversation, Session, Message]:
    """One chat turn. Stores the owner's message, runs the agent as a Session, then
    stores the agent's reply. Returns (conversation, the run, agent's Message)."""
    thread_id = ensure_agent_thread(repo, agent)  # agent's one memory thread
    conversation = get_or_create_direct_conversation(repo, owner, agent, thread_id)

    repo.add_message(
        Message(from_member_id=owner.id, text=text, conversation_id=conversation.id)
    )

    # the agent's own run — separate from the chat turns, with a lifecycle
    session = repo.add_session(
        Session(
            agent_id=agent.id,
            thread_id=thread_id,
            conversation_id=conversation.id,
            objective=CHAT_OBJECTIVE,
        )
    )
    with session_run(session, on_update=repo.update_session):
        answer = reply(thread_id, text)

    agent_message = repo.add_message(
        Message(from_member_id=agent.id, text=answer, conversation_id=conversation.id)
    )

    # activity stamps — set ke saath PERSIST bhi (add_* upsert hai)
    conversation.last_message_at = now_iso()
    repo.add_conversation(conversation)
    agent.last_active_at = now_iso()
    repo.add_member(agent)
    return conversation, session, agent_message
