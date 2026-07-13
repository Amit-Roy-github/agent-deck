"""ResearchFindings — the structured output shape."""

from __future__ import annotations

from agent_deck.agents.findings import Evidence, ResearchFindings


def test_findings_round_trip_through_plain_dict():
    findings = ResearchFindings(
        objective="What is X?",
        summary="X is Y.",
        evidence=[Evidence(claim="X is Y", detail="source says so", source_url="https://x")],
        sources=["https://x"],
    )
    as_dict = findings.model_dump()
    assert as_dict["objective"] == "What is X?"
    assert as_dict["evidence"][0]["source_url"] == "https://x"
    assert ResearchFindings(**as_dict) == findings  # JSON-portable round trip


def test_findings_default_to_empty_collections():
    findings = ResearchFindings(objective="o", summary="s")
    assert findings.evidence == []
    assert findings.sources == []
