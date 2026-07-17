"""HTTP API layer — FastAPI app the UI (and Swagger /docs) talks to."""

from agent_deck.api.app import create_app

__all__ = ["create_app"]
