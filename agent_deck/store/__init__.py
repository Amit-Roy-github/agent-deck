"""Persistence layer — the store behind the domain.

``Repository`` is the interface the app codes against. Two implementations:
``InMemoryRepository`` (keyless, for tests / zero-setup runs) and
``MongoRepository`` (Atlas/local Mongo). ``build_repository`` picks one the same
way the checkpointer does: Mongo when a URI is given, in-memory otherwise.
"""

from agent_deck.config import DEFAULT_DB_NAME
from agent_deck.store.repository import InMemoryRepository, Repository


def build_repository(
    mongo_uri: str | None = None, *, db_name: str = DEFAULT_DB_NAME
) -> Repository:
    """Mongo-backed repository if a URI is given, else in-memory (lazy import,
    so pymongo is only touched when actually used)."""
    if not mongo_uri:
        return InMemoryRepository()

    from pymongo import MongoClient

    from agent_deck.store.mongo import MongoRepository

    return MongoRepository(MongoClient(mongo_uri), db_name=db_name)


__all__ = ["Repository", "InMemoryRepository", "build_repository"]
