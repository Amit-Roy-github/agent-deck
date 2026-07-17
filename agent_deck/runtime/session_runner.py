"""Session runner — one objective, one agent run, one session record.

Orchestration only: it owns the session lifecycle (PENDING -> RUNNING ->
COMPLETED/FAILED) and delegates the actual thinking to a ``Researcher``. Because
it depends on the ``Researcher`` interface (not on LangGraph), it is fully
testable with a stub and unaware of which model/provider runs underneath.
"""

from __future__ import annotations

from agent_deck.agents.findings import ResearchFindings
from agent_deck.agents.research_agent import Researcher
from agent_deck.domain.models import Session
from agent_deck.runtime.lifecycle import session_run


def run_research_session(
    objective: str,
    researcher: Researcher,
    *,
    channel_id: str,
    agent_id: str,
    thread_id: str,
) -> tuple[Session, ResearchFindings]:
    """Run one research objective and return the session record + findings.

    Lifecycle (RUNNING -> COMPLETED/FAILED + re-raise) ``session_run`` sambhalta
    hai — wahi ek implementation jo chat bhi use karta hai.
    """
    session = Session(
        channel_id=channel_id,
        agent_id=agent_id,
        thread_id=thread_id,
        objective=objective,
    )
    with session_run(session):
        findings = researcher(objective, thread_id=thread_id)
    return session, findings
