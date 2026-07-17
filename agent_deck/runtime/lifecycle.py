"""Session lifecycle — RUNNING -> COMPLETED/FAILED ka EK implementation.

Pehle ye dance do jagah copy tha (chat + research runner) aur drift bhi ho gaya
tha (``completed_at`` ek mein stamp hota tha, doosre mein nahi). Ab dono yahi
context manager use karte hain — transition ka sach ek hi jagah.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager

from agent_deck.clock import now_iso
from agent_deck.domain.models import Session
from agent_deck.enums import SessionStatus


@contextmanager
def session_run(
    session: Session, on_update: Callable[[Session], object] | None = None
) -> Iterator[Session]:
    """Ek agent run ke around ka lifecycle: enter par RUNNING; exception par
    FAILED (re-raise); warna COMPLETED — ``completed_at`` hamesha stamp hota.
    ``on_update`` har transition ko store tak pahunchata (e.g.
    ``repo.update_session``); na do to sirf object mutate hota hai."""

    def push() -> None:
        if on_update is not None:
            on_update(session)

    session.status = SessionStatus.RUNNING
    push()
    try:
        yield session
    except Exception:
        session.status = SessionStatus.FAILED
        session.completed_at = now_iso()
        push()
        raise
    session.status = SessionStatus.COMPLETED
    session.completed_at = now_iso()
    push()
