"""The research agent — a LangGraph ReAct agent that searches then synthesizes.

Base is plain LangGraph ``create_agent`` (verified decision: not deepagents — we
own orchestration/permissions ourselves). It is given one tool (``web_search``)
and forced to answer in the ``ResearchFindings`` shape via ``response_format``.
"""

from __future__ import annotations

from collections.abc import Callable

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver

from agent_deck.agents.findings import ResearchFindings
from agent_deck.tools.web_search import (
    DuckDuckGoSearchProvider,
    SearchProvider,
    make_web_search_tool,
)

RESEARCH_SYSTEM_PROMPT = """\
You are a research agent. Given an objective, investigate it thoroughly using \
the web_search tool, then synthesize a clear, cited answer.

Rules:
- Never guess. Every claim must be backed by a source you actually found.
- Search multiple angles before concluding; prefer primary/official sources.
- Return structured findings: a concise summary, a list of evidence (each with \
a claim, its supporting detail, and the source URL), and the list of sources.\
"""

# A researcher takes an objective + a thread_id (its resumable session handle)
# and returns validated findings. Decouples the session runner from LangGraph.
Researcher = Callable[..., ResearchFindings]


def build_research_agent(
    model: str | BaseChatModel,
    *,
    search_provider: SearchProvider | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Build the compiled research agent.

    ``model`` is a chat model or a ``"provider:model"`` string. ``search_provider``
    defaults to keyless DuckDuckGo. ``checkpointer`` persists per-thread memory.
    """
    provider = search_provider or DuckDuckGoSearchProvider()
    return create_agent(
        model,
        tools=[make_web_search_tool(provider)],
        system_prompt=RESEARCH_SYSTEM_PROMPT,
        response_format=ResearchFindings,
        checkpointer=checkpointer,
    )


def make_researcher(agent) -> Researcher:
    """Adapt a compiled agent into a ``Researcher`` callable.

    Runs the objective under the given ``thread_id`` (LangGraph's session handle)
    and returns the validated ``ResearchFindings`` structured response.
    """

    def research(objective: str, *, thread_id: str) -> ResearchFindings:
        config = {"configurable": {"thread_id": thread_id}}
        result = agent.invoke(
            {"messages": [{"role": "user", "content": objective}]},
            config=config,
        )
        return result["structured_response"]

    return research
