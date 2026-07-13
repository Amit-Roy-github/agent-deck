"""build_checkpointer — Mongo when a URI is given, in-memory otherwise."""

from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver

from agent_deck.memory.checkpointer import build_checkpointer


def test_no_uri_falls_back_to_in_memory():
    assert isinstance(build_checkpointer(None), InMemorySaver)
    assert isinstance(build_checkpointer(""), InMemorySaver)


def test_uri_routes_to_mongo_saver(monkeypatch):
    # MongoDBSaver connects on construction (index setup), so we patch it and
    # the client to verify routing + args without touching a real server.
    captured = {}

    class FakeMongoClient:
        def __init__(self, uri):
            captured["uri"] = uri

    class FakeMongoDBSaver:
        def __init__(self, client, db_name=None):
            captured["client"] = client
            captured["db_name"] = db_name

    monkeypatch.setattr("pymongo.MongoClient", FakeMongoClient)
    monkeypatch.setattr("langgraph.checkpoint.mongodb.MongoDBSaver", FakeMongoDBSaver)

    result = build_checkpointer("mongodb://example:27017", db_name="agent_deck_test")

    assert isinstance(result, FakeMongoDBSaver)
    assert captured["uri"] == "mongodb://example:27017"
    assert captured["db_name"] == "agent_deck_test"
    assert isinstance(captured["client"], FakeMongoClient)
