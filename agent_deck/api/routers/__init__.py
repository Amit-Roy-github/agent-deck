"""Resource routers — ``app.py`` inhe ek loop mein include karta hai.
Naya resource = naya module yahan + is list mein ek entry, bas."""

from agent_deck.api.routers import chat, conversations, members, ownerships, sessions

ALL_ROUTERS = [
    members.router,
    ownerships.router,
    chat.router,
    conversations.router,
    sessions.router,
]

__all__ = ["ALL_ROUTERS"]
