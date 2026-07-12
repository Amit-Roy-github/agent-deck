# Agent Deck — Architecture

> A control deck for AI teams: a **channel = team** where a **manager** (human or agent) runs a mix of **agents and humans**, with first-class **ownership/permissions** (manager owns its agents; an agent owns only itself). Multi-agent, multi-provider.

---

## Locked decisions

| Area | Choice | Why |
|---|---|---|
| Language | **Python** | AI ecosystem (LangGraph/LangChain/deepagents) sabse mature Python mein |
| Agent framework | **LangGraph + LangChain** (+ deepagents optional) | Ready-made loop, context, memory, multi-agent, HITL |
| Providers | **LangChain models** — Claude / OpenAI / Gemini / local | Multi-provider, per-agent model swap |
| Database | **MongoDB** | Baaki projects Mongo (consistency); Python mein official LangGraph Mongo checkpointer |
| Host | **GCP Cloud Run** | Browser-only access, zero local setup, always-free tier |
| Default model | `claude-opus-4-8` | Strong default; sasta kaam saste model pe route |

---

## The concept (what we're building)

- **Team = Channel** — ek hi cheez, ek shared communication space.
- **Member** = base type; `kind ∈ {HUMAN, AGENT}`. Dono equal citizens.
- **Manager** — team chalata; shuru mein human, baad mein agent bhi.
- **Communication** — koi bhi member kisi se bhi (agent↔agent, agent↔human).
- **Permissions (first-class, our moat):** manager → controls whole channel + owned agents. Agent → controls only itself.

Ye combo (permission-driven ownership + human/agent interchangeable + team=channel) kisi framework mein ready nahi — **wahi hum khud banate hain**. Baaki plumbing LangChain-stack se.

---

## System architecture

```
Browser (koi bhi khole, zero setup)
   │  HTTPS
   ▼
┌─────────────────────────── Cloud Run ───────────────────────────┐
│  Agent Deck app (Python — FastAPI)                              │
│                                                                 │
│   API / WebSocket                                               │
│      ├─ Domain layer   → members, channels, ownership, messages │
│      ├─ Orchestration  → manager assigns objective → session    │
│      └─ Agent runtime  → LangGraph graph (per agent)            │
│                              └─ LangChain models (provider swap) │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                        ┌── MongoDB ──┐
                        │ Domain data │  members / channels / ownership / messages / sessions
                        │ Agent memory│  checkpoints / store  (LangGraph-managed)
                        └─────────────┘
                               │
                     External providers (via LangChain)
                     Claude API · OpenAI · Gemini · ...
```

**Tumhara product (channel/manager/ownership) tumhare Cloud Run pe. Sirf model inference bahar (providers) jaata.**

---

## Data model (MongoDB)

### Domain collections (we design)
```
members         { _id, kind: HUMAN|AGENT, name, role: MANAGER|MEMBER, managerId }
channels        { _id, name, ownerId }                    ← team = channel
channel_members { channelId, memberId }
ownership       { managerId, agentId }                    ← manager owns agent
agent_configs   { memberId, provider, model, systemPrompt, tools }
messages        { channelId, fromId, text, ts }           ← channel chat log
sessions        { _id, channelId, agentId, threadId, objective, status }
```

### Memory collections (LangGraph auto-manages)
```
checkpoints     { threadId → session state (conversation memory) }
checkpoint_writes
store           { namespace → long-term facts (cross-session) }
```

**Link:** `sessions.threadId` → LangGraph checkpoint. Domain (kaun/kahan) + memory (kya soch raha) jude.

### Permissions (enum, no string literals)
```
Permission: CONTROL_SELF | CONTROL_AGENT | CONTROL_CHANNEL | SEND_MESSAGE
Rule:  MANAGER → CONTROL_CHANNEL + CONTROL_AGENT (owned) + CONTROL_SELF + SEND_MESSAGE
       MEMBER  → CONTROL_SELF + SEND_MESSAGE
can(actor, action, target) → bool     ← single source of truth
```

---

## Memory & context (how "Claude-Code-like" behaviour comes)

- Raw model stateless hai — LangGraph iska harness deta.
- **Short-term (per session):** LangGraph **checkpointer** (MongoDB) — har session ka state `threadId` se save/load.
- **Long-term (cross-session):** LangGraph **store** — agent learnings/facts.
- **Multi-agent = multi-session:** sab ek Mongo mein, `threadId`/namespace se alag. 1000 sessions = 1000 threadIds, ek DB.

---

## Multi-provider & cost control

- **Provider swap:** LangChain models — agent ka `agent_configs.provider/model` se model choose. Ek interface, koi bhi provider.
- **Cost lever (manager = router):**
  - Simple kaam (summarize/classify) → sasta model (Haiku / cheaper provider)
  - Hard reasoning → Opus/Fable
  - **Prompt caching** repeated context pe (~90% saving on Claude)
  - **Effort control** (`low/medium`) routine kaam pe

---

## MVP scope (Phase 1 — one real research agent)

```
[You = Manager]  ──objective (research topic)──►  [Research Agent (real LLM)]
       ▲                                                  │
       └──────── findings posted in channel ◄─────────────┘
```

- 1 channel, 1 human manager (tum), 1 real research agent
- Objective type = **research** (coding-type baad mein)
- Ownership/permission skeleton light but correct (taaki agent #2, #3 add ho sakein)

---

## Build phases

**Phase 0 — Design lock** ✅ (this file)

**Phase 1 — Domain + permission engine**
- `Member`, `Channel`, `Message`, `Session`, `Permission` schemas
- `can(actor, action, target)` — enum-driven, DB-independent, testable

**Phase 2 — Research agent (real)**
- LangGraph graph + LangChain model (Claude default)
- Objective le → research (search → synthesize) → structured findings → channel post
- MongoDB checkpointer wired

**Phase 3 — Channel runtime + objective intake**
- Manager objective daale → session bane → agent chale → findings channel mein
- Persist + history

**Phase 4 — Provider layer**
- OpenAI/Gemini pluggable behind LangChain; per-agent model config

**Phase 5 — GCP deploy**
- Cloud Run + MongoDB (Atlas free tier); browser URL

**Phase 6 — Frontend + more agents**
- Channel UI, member list, controls; agent #2/#3, coding objectives, agent-as-manager

---

## Open items to verify before build (no guessing)

1. **`langgraph-checkpoint-mongodb`** — exact package name, install, API (Python). Confirm maintained + version.
2. **deepagents vs plain LangGraph** — research agent ke liye konsa base (deepagents ready-made harness deta; LangGraph zyada control).
3. **MongoDB Atlas free tier** vs GCP-native — cheapest path for Cloud Run + Mongo.
4. **WebSocket vs SSE** on Cloud Run — channel realtime ke liye (Cloud Run dono support karta, but limits check).

---

## Related
- Prior-art comparison: `channel.md` (existing frameworks vs our concept)
