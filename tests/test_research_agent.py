"""build_research_agent — the graph assembles offline (no LLM call on build)."""

from __future__ import annotations

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from agent_deck.agents.research_agent import build_research_agent, make_researcher
from agent_deck.memory.checkpointer import build_checkpointer
from agent_deck.tools.web_search import SearchResult, StaticSearchProvider


def test_agent_compiles_with_model_tools_and_checkpointer():
    agent = build_research_agent(
        GenericFakeChatModel(messages=iter([])),
        search_provider=StaticSearchProvider([SearchResult("t", "https://x", "s")]),
        checkpointer=build_checkpointer(None),
    )
    nodes = set(agent.get_graph().nodes)
    assert {"model", "tools"} <= nodes  # web_search tool + model both wired
    assert hasattr(agent, "invoke")


def test_make_researcher_returns_callable():
    agent = build_research_agent(
        GenericFakeChatModel(messages=iter([])),
        search_provider=StaticSearchProvider([]),
    )
    assert callable(make_researcher(agent))
