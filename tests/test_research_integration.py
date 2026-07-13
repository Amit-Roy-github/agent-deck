"""End-to-end research run against a REAL Claude model + real DuckDuckGo search.

Skipped unless ANTHROPIC_API_KEY is set (keeps the default suite offline/free).
Run it with a key to prove the full Phase-2 flow: objective -> search ->
synthesize -> structured findings, memory persisted via the checkpointer.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="needs ANTHROPIC_API_KEY (real LLM call)",
)


def test_research_objective_end_to_end():
    from agent_deck.agents.research_agent import build_research_agent, make_researcher
    from agent_deck.config import build_chat_model
    from agent_deck.memory.checkpointer import build_checkpointer
    from agent_deck.runtime.session_runner import run_research_session

    agent = build_research_agent(
        build_chat_model(),
        checkpointer=build_checkpointer(os.getenv("MONGODB_URI")),
    )
    researcher = make_researcher(agent)

    session, findings = run_research_session(
        "What is the capital of France? Cite a source.",
        researcher,
        channel_id="chan",
        agent_id="agent",
        thread_id="thread-integration",
    )

    assert findings.summary
    assert findings.sources or findings.evidence
    assert session.status.value == "completed"
