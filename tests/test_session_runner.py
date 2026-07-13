"""run_research_session — session lifecycle orchestration (LLM-independent)."""

from __future__ import annotations

import pytest

from agent_deck.agents.findings import Evidence, ResearchFindings
from agent_deck.enums import SessionStatus
from agent_deck.runtime.session_runner import run_research_session


def test_successful_run_completes_session_and_returns_findings():
    findings = ResearchFindings(
        objective="obj",
        summary="done",
        evidence=[Evidence(claim="c", detail="d", source_url="https://x")],
    )
    seen = {}

    def researcher(objective, *, thread_id):
        seen["objective"] = objective
        seen["thread_id"] = thread_id
        return findings

    session, out = run_research_session(
        "obj", researcher, channel_id="chan", agent_id="ag", thread_id="thread-1"
    )

    assert out is findings
    assert session.status is SessionStatus.COMPLETED
    assert session.channel_id == "chan"
    assert session.agent_id == "ag"
    assert session.thread_id == "thread-1"
    # the runner passes the objective + thread through to the researcher
    assert seen == {"objective": "obj", "thread_id": "thread-1"}


def test_researcher_error_propagates():
    def researcher(objective, *, thread_id):
        raise RuntimeError("search failed")

    with pytest.raises(RuntimeError, match="search failed"):
        run_research_session(
            "obj", researcher, channel_id="c", agent_id="a", thread_id="t"
        )
