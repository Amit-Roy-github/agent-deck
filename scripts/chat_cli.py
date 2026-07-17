"""Interactive CLI chat — Agent Deck ko terminal se actually use karo.

Tum type karo, agent (Gemini) reply kare; har turn Conversation/Session/Message
ke roop mein store hota hai. ``MONGODB_URI`` set hai to sab Mongo (Atlas) mein
persist hota hai — members, chat history AUR agent ki memory (checkpoint) —
matlab band karke dobara kholo to wahi log, wahi history, wahi yaaddasht.
URI nahi hai to in-memory fallback (exit = fresh).

Run:
    ./.venv/bin/python scripts/chat_cli.py

Commands inside chat:
    /history   stored messages dikhao (store se wapas padh ke)
    /sessions  agent ke runs dikhao
    /exit      band karo (ya Ctrl+C / Ctrl+D)
"""

from __future__ import annotations

import time

from agent_deck.config import DEFAULT_GEMINI_MODEL, build_model_for_member, load_settings
from agent_deck.domain.models import Member, Ownership
from agent_deck.enums import AgentProvider, MemberKind
from agent_deck.memory.checkpointer import build_checkpointer
from agent_deck.runtime.chat import build_agent_reply, send_message
from agent_deck.store import Repository, build_repository

AGENT_MODEL = DEFAULT_GEMINI_MODEL


def get_or_create_member(repo: Repository, name: str, **kwargs) -> Member:
    """Naam se wapas utha lo (Mongo mein pehle se hai to), warna naya banao."""
    existing = repo.find_member_by_name(name)
    if existing is not None:
        return existing
    return repo.add_member(Member(name=name, **kwargs))


def show_history(repo: Repository, conversation_id: str, human: Member, agent: Member) -> None:
    messages = repo.list_messages(conversation_id)
    print(f"\n--- History ({len(messages)} messages, store se) ---")
    for msg in messages:
        who = human.name if msg.from_member_id == human.id else agent.name
        print(f"  [{msg.sequence_number}] {who}: {msg.text}")
    print()


def show_sessions(repo: Repository) -> None:
    sessions = repo.list_sessions()
    print(f"\n--- Sessions ({len(sessions)} agent runs) ---")
    for s in sessions:
        print(f"  run {s.id[:8]}  status={s.status.value}  started={s.created_at}")
    print()


def main() -> None:
    settings = load_settings()
    if not settings.google_api_key:
        raise SystemExit("GOOGLE_API_KEY nahi mili — .env mein daalo ya export karo.")

    repo = build_repository(settings.mongodb_uri, db_name=settings.mongodb_db_name)
    store_label = "Mongo (Atlas)" if settings.mongodb_uri else "in-memory"

    human_name = input("Tumhara naam: ").strip() or "Amit"
    agent_name = input("Agent ka naam: ").strip() or "Gyaani"

    human = get_or_create_member(repo, human_name, kind=MemberKind.HUMAN)
    agent = get_or_create_member(
        repo,
        agent_name,
        kind=MemberKind.AGENT,
        provider=AgentProvider.GEMINI,
        model=AGENT_MODEL,
        identity=f"Tum '{agent_name}' ho, {human_name} ka personal assistant. "
        "Hinglish mein chhota, seedha jawab do.",
    )
    if not repo.owns(human.id, agent.id):
        repo.add_ownership(Ownership(owner_id=human.id, agent_id=agent.id))

    reply = build_agent_reply(
        build_model_for_member(agent, settings),
        system_prompt=agent.identity,
        checkpointer=build_checkpointer(
            settings.mongodb_uri, db_name=settings.mongodb_db_name
        ),
    )

    print(f"\n{agent_name} taiyaar hai. Store: {store_label}. (/history /sessions /exit)\n")

    # purani DM hai to wahi utha lo — restart ke baad bhi wahi conversation
    existing = repo.find_direct_conversation(human.id, agent.id)
    conversation_id: str | None = existing.id if existing else None
    if conversation_id:
        old_count = len(repo.list_messages(conversation_id))
        print(f"(purani chat mili — {old_count} messages. /history se dekho)\n")

    while True:
        try:
            text = input(f"{human_name}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not text:
            continue
        if text == "/exit":
            break
        if text == "/history":
            if conversation_id is None:
                print("Abhi koi message nahi.\n")
            else:
                show_history(repo, conversation_id, human, agent)
            continue
        if text == "/sessions":
            show_sessions(repo)
            continue

        print(f"{agent_name} soch raha hai...", end="", flush=True)
        started = time.perf_counter()
        conversation, _session, agent_msg = send_message(
            repo, reply, owner=human, agent=agent, text=text
        )
        elapsed = time.perf_counter() - started
        conversation_id = conversation.id
        print(f"\r{agent_name} ({elapsed:.1f}s): {agent_msg.text}\n")

    # exit summary — store mein kya bana
    print("--- Store summary ---")
    print(f"Conversations: {len(repo.list_conversations())}")
    print(f"Sessions     : {len(repo.list_sessions())}")
    messages_count = len(repo.list_messages(conversation_id)) if conversation_id else 0
    print(f"Messages     : {messages_count}")
    if settings.mongodb_uri:
        print("(sab Mongo mein persist — dobara kholo, wahi milega)")
    else:
        print("(in-memory tha — MONGODB_URI set karo to persist hoga)")


if __name__ == "__main__":
    main()
