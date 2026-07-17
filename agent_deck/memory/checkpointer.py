"""Checkpointer — where an agent's conversation state (memory) is persisted.

A conversation is stored under its ``thread_id``; resuming with the same
thread_id restores full context. With a MongoDB URI we use the official
``MongoDBSaver`` (verified: langgraph-checkpoint-mongodb 0.4.0); without one we
fall back to an in-memory saver so the app runs locally with zero setup.
"""

from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from agent_deck.config import DEFAULT_DB_NAME


def build_checkpointer(
    mongo_uri: str | None = None,
    *,
    db_name: str = DEFAULT_DB_NAME,
) -> BaseCheckpointSaver:
    """Return a MongoDB-backed checkpointer if a URI is given, else in-memory.

    The MongoClient is lazy — constructing it does not connect until first use.
    """
    if not mongo_uri:
        return InMemorySaver()

    from langgraph.checkpoint.mongodb import MongoDBSaver
    from pymongo import MongoClient

    return MongoDBSaver(MongoClient(mongo_uri), db_name=db_name)
