"""Agents — the research agent and its adapters."""

from agent_deck.agents.findings import Evidence, ResearchFindings
from agent_deck.agents.research_agent import build_research_agent, make_researcher

__all__ = [
    "ResearchFindings",
    "Evidence",
    "build_research_agent",
    "make_researcher",
]
