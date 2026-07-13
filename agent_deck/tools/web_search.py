"""Web search — a pluggable provider behind one LangChain tool.

The agent only ever sees the ``web_search`` tool; how results are fetched is a
swappable ``SearchProvider``. Default is DuckDuckGo (real results, no API key),
so only the LLM needs credentials. Tests inject ``StaticSearchProvider`` for
deterministic, offline runs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from langchain_core.tools import BaseTool, tool


@dataclass
class SearchResult:
    """One search hit — provider-agnostic shape."""

    title: str
    url: str
    snippet: str


@runtime_checkable
class SearchProvider(Protocol):
    """Anything that can turn a query into results."""

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]: ...


class DuckDuckGoSearchProvider:
    """Keyless real web search via DuckDuckGo (the ``ddgs`` package)."""

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        from ddgs import DDGS

        rows = DDGS().text(query, max_results=max_results)
        return [
            SearchResult(
                title=row.get("title", ""),
                url=row.get("href", "") or row.get("url", "") or row.get("link", ""),
                snippet=row.get("body", "") or row.get("snippet", ""),
            )
            for row in rows
        ]


class StaticSearchProvider:
    """Deterministic provider for tests — returns preset results, no network."""

    def __init__(self, results: Sequence[SearchResult]) -> None:
        self._results = list(results)

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return self._results[:max_results]


def make_web_search_tool(provider: SearchProvider) -> BaseTool:
    """Build the ``web_search`` tool bound to a given provider."""

    @tool
    def web_search(query: str) -> str:
        """Search the web for a query and return titled results with URLs and snippets."""
        results = provider.search(query)
        if not results:
            return "No results found."
        return "\n\n".join(
            f"{result.title}\n{result.url}\n{result.snippet}" for result in results
        )

    return web_search
