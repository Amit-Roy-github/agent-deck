"""End-to-end slice (no channel): members + ownership + owner<->agent chat, stored.

Proves:
  1. human member banta + store hota
  2. agent member (Gemini) banta + store hota
  3. ownership (human -> agent) store hota
  4. owner apne agent se chat karta (Gemini reply)
  5. har chat turn store hota (store se wapas padh ke dikhaya)
  6. agent ka session store hota (thread_id + status)

Run:
    export GOOGLE_API_KEY=...        # ya .env mein GOOGLE_API_KEY=...
    ./.venv/bin/python scripts/member_chat_test.py
"""

from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver

from agent_deck.config import build_model_for_member, load_settings
from agent_deck.domain.models import Member, Ownership
from agent_deck.enums import AgentProvider, MemberKind
from agent_deck.runtime.chat import build_agent_reply, send_message
from agent_deck.store.repository import InMemoryRepository

AGENT_MODEL = "gemini-3.5-flash"


def line(char: str = "-") -> None:
    print(char * 60)


def main() -> None:
    settings = load_settings()
    if not settings.google_api_key:
        raise SystemExit("GOOGLE_API_KEY nahi mili — .env mein daalo ya export karo.")

    repo = InMemoryRepository()

    # 1. human member
    human = repo.add_member(Member(name="Amit", kind=MemberKind.HUMAN))

    # 2. agent member (Gemini)
    agent = repo.add_member(
        Member(
            name="Gyaani",
            kind=MemberKind.AGENT,
            provider=AgentProvider.GEMINI,
            model=AGENT_MODEL,
            identity="Tum 'Gyaani' ho, Amit ka personal assistant. "
            "Hinglish mein chhota, seedha jawab do.",
        )
    )

    # 3. ownership: human owns the agent
    repo.add_ownership(Ownership(owner_id=human.id, agent_id=agent.id))

    print(f"Human member : {human.name}  (id {human.id[:8]}, kind {human.kind.value})")
    print(f"Agent member : {agent.name}  (id {agent.id[:8]}, {agent.provider.value}/{agent.model})")
    print(f"Ownership    : {human.name} -> {agent.name}  (repo.owns = {repo.owns(human.id, agent.id)})")

    # 4. owner chats with the agent (each turn stored)
    reply = build_agent_reply(
        build_model_for_member(agent, settings),
        system_prompt=agent.identity,
        checkpointer=InMemorySaver(),
    )
    turns = [
        "Namaste! Mera naam Amit hai.",
        "Ek chhoti Python tip do.",
        "Mera naam kya tha?",  # memory check
    ]

    line("=")
    print("CHAT")
    line("=")
    for text in turns:
        conversation, session, agent_msg = send_message(
            repo, reply, owner=human, agent=agent, text=text
        )
        print(f"\n{human.name}: {text}")
        print(f"{agent.name}: {agent_msg.text}")

    # ---- READ BACK FROM STORE (proof: sab store hua) ----
    line("=")
    print("STORE SE WAPAS PADHA")
    line("=")

    print(f"\nMembers stored: {len(repo.list_members())}")
    for m in repo.list_members():
        print(f"  - {m.kind.value:5} {m.name}")

    print(f"\nOwnerships stored: {len(repo.list_ownerships())}")
    for o in repo.list_ownerships():
        print(f"  - owner {o.owner_id[:8]} -> agent {o.agent_id[:8]}")

    # CONVERSATION (chat container) — alag layer
    conversations = repo.list_conversations()
    print(f"\nConversations stored: {len(conversations)}   (chat container / DM)")
    conv = conversations[0]
    print(f"  - conv {conv.id[:8]}  {conv.member_a_id[:8]} <-> {conv.member_b_id[:8]}  thread={conv.thread_id[:8]}")

    # SESSIONS (agent runs) — alag layer, har reply pe ek
    sessions = repo.list_sessions()
    print(f"\nSessions stored: {len(sessions)}   (agent RUN per reply, lifecycle)")
    for s in sessions:
        print(f"  - run {s.id[:8]}  agent={s.agent_id[:8]}  status={s.status.value}  obj='{s.objective}'")

    # MESSAGES (visible chat turns)
    messages = repo.list_messages(conv.id)
    print(f"\nMessages stored (conv {conv.id[:8]}): {len(messages)}   (visible turns)")
    for msg in messages:
        who = "Amit " if msg.from_member_id == human.id else "Gyaani"
        print(f"  [{msg.sequence_number}] {who}: {msg.text[:55]}")

    # ---- checks ----
    line("=")
    ok_conv = len(conversations) == 1                   # ek hi DM container
    ok_runs = len(sessions) == len(turns)               # har turn = ek agent run
    ok_done = all(s.status.value == "completed" for s in sessions)
    ok_msgs = len(messages) == len(turns) * 2           # har turn = 2 messages
    ok_memory = "amit" in messages[-1].text.lower()     # agent ne naam yaad rakha
    print("Ek Conversation (DM)        :", "✅" if ok_conv else "❌")
    print(f"Sessions = turns (runs)     :", "✅" if ok_runs else "❌", f"({len(sessions)})")
    print("Sab runs completed          :", "✅" if ok_done else "❌")
    print(f"Messages = 2x turns         :", "✅" if ok_msgs else "❌", f"({len(messages)})")
    print("Agent ne naam yaad rakha    :", "✅" if ok_memory else "❌")
    all_ok = ok_conv and ok_runs and ok_done and ok_msgs and ok_memory
    print("\nSAB SAHI ✅" if all_ok else "\nKUCH GADBAD ❌")


if __name__ == "__main__":
    main()
