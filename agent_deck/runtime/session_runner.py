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
from agent_deck.enums import SessionStatus


def run_research_session(
    objective: str,
    researcher: Researcher,
    *,
    channel_id: str,
    agent_id: str,
    thread_id: str,
) -> tuple[Session, ResearchFindings]:
    """Run one research objective and return the session record + findings.

    The session is marked RUNNING before the agent starts and COMPLETED on
    success; on any error it is marked FAILED and the error is re-raised.
    """
    session = Session(
        channel_id=channel_id,
        agent_id=agent_id,
        thread_id=thread_id,
        objective=objective,
        status=SessionStatus.RUNNING,
    )
    try:
        findings = researcher(objective, thread_id=thread_id)
    except Exception:
        session.status = SessionStatus.FAILED
        raise

    session.status = SessionStatus.COMPLETED
    return session, findings
