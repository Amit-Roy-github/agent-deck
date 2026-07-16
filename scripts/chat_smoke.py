"""Quick smoke test: chat with ONE agent (Gemini), no research, no tools.

Proves the whole agent path works end-to-end:
  provider (Gemini) -> create_agent -> checkpointer memory -> reply.

Two turns on the SAME thread_id check that memory persists:
  turn 1 tells it a name, turn 2 asks for it back.

Run:
    # key do (in dono mein se ek):
    export GOOGLE_API_KEY=...            # ya .env mein GOOGLE_API_KEY=...
    ./.venv/bin/python scripts/chat_smoke.py
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

MODEL = "gemini-3.5-flash"  # sasta + fast; galat nikle to list_models se badal lenge
THREAD_ID = "chat-smoke-1"


def load_key() -> str:
    """GOOGLE_API_KEY env se, warna .env se (bina extra dependency ke)."""
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        return key
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip().startswith("GOOGLE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("GOOGLE_API_KEY nahi mili — export karo ya .env mein daalo.")


def build_chat_agent():
    model = ChatGoogleGenerativeAI(model=MODEL, google_api_key=load_key())
    # no tools, no response_format -> plain conversational agent
    return create_agent(
        model,
        tools=[],
        system_prompt="Tum ek madadgar assistant ho. Chhota, seedha jawab do.",
        checkpointer=InMemorySaver(),
    )


def message_text(content) -> str:
    """Reply ka text nikaalo. Gemini 3.x / Claude 'content blocks' ki LIST deta
    ([{'type':'text','text':...}]), purane models plain str. Dono handle karo."""
    if isinstance(content, str):
        return content
    parts = [
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in content
    ]
    return "".join(parts)


def say(agent, text: str) -> str:
    """Ek message bhejo, reply string wapas lo (same thread = memory rehti)."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": text}]},
        config={"configurable": {"thread_id": THREAD_ID}},
    )
    return message_text(result["messages"][-1].content)


def main() -> None:
    agent = build_chat_agent()
    print(f"[model: {MODEL}]\n")

    q1 = "Mera naam Amit hai. Hi bolo."
    print("You:", q1)
    print("AI :", say(agent, q1), "\n")

    q2 = "Mera naam kya hai?"
    print("You:", q2)
    reply = say(agent, q2)
    print("AI :", reply, "\n")

    # memory check
    ok = "amit" in reply.lower()
    print("✅ Memory kaam kar rahi (naam yaad raha)" if ok
          else "⚠️ Naam yaad nahi raha — memory/thread check karo")


if __name__ == "__main__":
    main()
