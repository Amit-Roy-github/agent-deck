"""Structured research output — the shape a research agent must return.

A pydantic model so it can be handed to ``create_agent(response_format=...)``:
the agent is forced to answer in this shape, and the result is validated for us.
Every claim carries its evidence and a source URL (no-guessing: cite everything).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """One supported claim from the research."""

    claim: str = Field(description="A single factual claim the research established.")
    detail: str = Field(description="The supporting detail / what the source says.")
    source_url: str = Field(description="URL of the source backing this claim.")


class ResearchFindings(BaseModel):
    """The complete result of one research objective."""

    objective: str = Field(description="The objective that was researched.")
    summary: str = Field(description="A concise synthesis answering the objective.")
    evidence: list[Evidence] = Field(
        default_factory=list, description="Claims, each with detail + source."
    )
    sources: list[str] = Field(
        default_factory=list, description="All distinct source URLs consulted."
    )
