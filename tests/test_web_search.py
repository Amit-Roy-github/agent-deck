"""web_search tool — provider is pluggable; tested with the static provider."""

from __future__ import annotations

from agent_deck.tools.web_search import (
    SearchResult,
    StaticSearchProvider,
    make_web_search_tool,
)


def test_tool_formats_title_url_and_snippet():
    provider = StaticSearchProvider(
        [
            SearchResult("First", "https://a.example", "snippet one"),
            SearchResult("Second", "https://b.example", "snippet two"),
        ]
    )
    web_search = make_web_search_tool(provider)
    out = web_search.invoke({"query": "anything"})
    for expected in ("First", "https://a.example", "snippet one", "Second"):
        assert expected in out


def test_tool_handles_no_results():
    web_search = make_web_search_tool(StaticSearchProvider([]))
    assert "No results" in web_search.invoke({"query": "x"})


def test_static_provider_respects_max_results():
    provider = StaticSearchProvider(
        [SearchResult(f"T{i}", "u", "s") for i in range(10)]
    )
    assert len(provider.search("q", max_results=3)) == 3


def test_tool_is_named_web_search():
    web_search = make_web_search_tool(StaticSearchProvider([]))
    assert web_search.name == "web_search"
