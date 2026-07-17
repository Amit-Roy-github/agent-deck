"""App bootstrap — SIRF server ka kaam: app banao, middleware lagao, dependencies
wire karo (app.state), routers jodo. Koi route/business logic yahan nahi —
routes ``routers/`` mein, asli kaam ``runtime/`` + ``store/`` mein.

Run:
    ./.venv/bin/uvicorn agent_deck.api.app:app --reload --port 8000
Then open http://localhost:8000/docs (Swagger UI) to try every endpoint.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_deck.api.routers import ALL_ROUTERS
from agent_deck.config import Settings, load_settings
from agent_deck.memory.checkpointer import build_checkpointer
from agent_deck.runtime.agents import AgentRuntime
from agent_deck.store import build_repository

# Vite dev server (React UI) — prod mein UI aur API same origin honge
DEV_UI_ORIGINS = ["http://localhost:5173"]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    app = FastAPI(title="Agent Deck", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEV_UI_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # dependencies — routers inhe deps.py ke through Depends() se lete hain
    app.state.repo = build_repository(settings.mongodb_uri, db_name=settings.mongodb_db_name)
    app.state.agent_runtime = AgentRuntime(
        settings,
        build_checkpointer(settings.mongodb_uri, db_name=settings.mongodb_db_name),
    )

    for router in ALL_ROUTERS:
        app.include_router(router)

    return app


app = create_app()
