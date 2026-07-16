"""Persistence layer — the store behind the domain.

``Repository`` is the interface the app codes against; ``InMemoryRepository`` is
the keyless implementation used for local runs and tests. A MongoDB-backed
implementation drops in later behind the same interface (same pattern as the
checkpointer: Mongo when a URI is given, in-memory otherwise).
"""

from agent_deck.store.repository import InMemoryRepository, Repository

__all__ = ["Repository", "InMemoryRepository"]
