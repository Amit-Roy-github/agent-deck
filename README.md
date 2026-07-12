# Agent Deck

A control deck for AI teams. **Channel = team**; a **manager** (human or agent, interchangeable) runs a mix of agents + humans (one base member type). First-class **ownership/permissions** are the moat.

## Docs
- `architecture.md` — full design (stack, schema, permission engine, build phases)
- `channel.md` — prior-art comparison (deep-researched)
- `findings.md` — running log of all decisions + why

## Stack (locked)
Python · LangGraph + LangChain · MongoDB · GCP Cloud Run · default model `claude-opus-4-8`
