# Agent Deck — Findings & Decisions Log

> Sab reusable learnings, decisions, aur unke **why** — taaki aage koi cheez dobara na sochni pade / re-litigate na ho. Jab bhi kuch naya pata chale ya decide ho, yahan add karo.

Related docs: `architecture.md` (full design), `channel.md` (prior-art comparison).

---

## 1. Core concept (what makes Agent Deck unique)

- **Team = Channel** — ek object, ek shared communication space.
- **Member** = base type; `kind ∈ {HUMAN, AGENT}` — dono equal citizens.
- **Manager** — human ya agent, **interchangeable** (same slot).
- **Communication** — any member ↔ any member (agent↔agent, agent↔human).
- **Ownership/permissions (first-class = our moat):** manager owns channel + its agents; agent owns only itself.

**Prior-art verdict (from `channel.md`, deep-researched):** ye exact combo — permission-driven ownership + human/agent interchangeable manager + team=channel — **kisi framework/product mein ready nahi.** Tukde exist karte hain, combo nahi. So ye layer hum khud banate hain; baaki plumbing ready-made se.

---

## 2. Key decisions + WHY (don't re-litigate)

| Decision | Choice | Why |
|---|---|---|
| Language | **Python** | AI ecosystem (LangGraph/LangChain/deepagents) Python-first + sabse mature. (User usually Node/TS, but yahan Python better.) |
| Agent framework | **LangGraph + LangChain** (+ deepagents optional) | Raw model stateless — ye harness (loop/context/memory) deta |
| Providers | **LangChain models** | Multi-provider (Claude/OpenAI/Gemini) ek interface pe; per-agent swap |
| DB | **MongoDB** | Consistency (baaki projects Mongo); Python mein official `langgraph-checkpoint-mongodb` |
| Host | **GCP Cloud Run** | Browser-only, zero local setup, always-free tier |
| Default model | `claude-opus-4-8` | Strong default; sasta kaam saste model pe route |

---

## 3. Why NOT Managed Agents (CMA / Anthropic)

- CMA sirf **Claude models**, sirf **Anthropic infra** pe chalata.
- **Multi-provider requirement ke saath incompatible** → ruled out.
- CMA ka convenience (loop + memory free) tabhi milta jab Anthropic-locked ho.
- **Takeaway:** koi bhi Anthropic-only hosted solution multi-provider goal se conflict karta. Own harness zaroori.

---

## 4. Memory / context — how raw model gets "Claude-Code-like"

- **Raw Messages API stateless hai** — har call pe pura history bhejo, khud kuch yaad nahi.
- Claude Code ka context-mgmt/tool-loop/memory/compaction = ek **harness layer** upar. LangGraph wahi deta.
- **LangGraph 2 memory types:**
  - **Short-term (per session) = checkpointer** — har session ka state `thread_id` se save/load. Backend: MongoDB (`langgraph-checkpoint-mongodb`). `MemorySaver` sirf RAM (testing).
  - **Long-term (cross-session) = store** — namespaced key-value, agent learnings/facts.
- **Multi-agent = multi-session:** sab ek DB mein, `thread_id`/namespace se alag. 1000 sessions = 1000 threadIds, ek Mongo.

---

## 5. Two kinds of data (both in one Mongo)

- **Domain data (hum design karte):** `members, channels, channel_members, ownership, agent_configs, messages, sessions`
- **Agent memory (LangGraph auto-manage):** `checkpoints, checkpoint_writes, store`
- **Link:** `sessions.threadId` → LangGraph checkpoint. Domain (kaun/kahan) + memory (kya soch raha) jude.

---

## 6. Mongo vs Postgres — resolved to Mongo

- Postgres pehle lean tha kyunki: LangGraph checkpointer first-class Postgres pe, aur ownership model relational.
- **But:** ownership relations **shallow** hain (manager→agents 1 level, channel→members) — Mongo `$lookup`/references se easily handle. Extra effort minor.
- **Deciding flips:**
  1. Baaki projects Mongo → consistency (ek DB, ek skillset, ek ops) — real value
  2. **Python** mein Mongo checkpointer **official** (`langgraph-checkpoint-mongodb`) — JS wala weak-maturity concern gayab ho gaya
- Postgres free hosting problem nahi tha (Neon/Supabase free) — but consistency ne Mongo jitwaya.
- **Rule of thumb:** deep-relational + zero-friction LangGraph memory chahiye → Postgres. Consistency + document-shape events + Python → Mongo.

---

## 7. Multi-provider & cost control

- **Provider swap:** LangChain models; agent ka `agent_configs.provider/model` se choose.
- **Cost = biggest lever (manager acts as router):**
  - Simple kaam (summarize/classify) → sasta model (Haiku / cheaper provider)
  - Hard reasoning → Opus/Fable
  - **Prompt caching** repeated context pe → ~90% saving (Claude)
  - **Effort control** (`low/medium`) routine kaam pe → kam tokens

---

## 8. Claude API facts worth remembering (from claude-api skill)

- **Current models:** `claude-fable-5` (most capable, but 30-day retention required + priciest), `claude-opus-4-8` (default pick), `claude-sonnet-5`, `claude-haiku-4-5` (cheap/fast). Use exact IDs, no date suffixes.
- **Thinking:** 4.6+ models use `thinking: {type: "adaptive"}` — `budget_tokens` 400s on Fable5/Opus4.8/4.7. Effort via `output_config: {effort: low|medium|high|xhigh|max}`.
- **`max_tokens > ~16k` → must stream** (SDK HTTP timeout).
- **Stateless API** — send full history each call (relevant to why we need LangGraph).
- **CMA self-hosted sandbox** exists (loop on Anthropic, tools on your infra, outbound-only poll) — but still Claude-only, so not for us.
- **Server-side compaction / context editing** are opt-in beta params usable even in your own loop — could reduce our own context-mgmt work on Claude calls (dusre providers pe khud manage).

---

## 9. Frameworks landscape (from prior-art research)

- **LangChain** = provider abstraction (multi-provider) + building blocks.
- **LangGraph** = multi-agent orchestration, state, supervisor pattern, HITL built-in (`interrupt()`). Supervisor = LLM (not human); network/swarm topology allows direct agent↔agent.
- **deepagents** = ready-made Claude-Code-like agent (planning, subagents, filesystem, HITL) on top of LangGraph. HITL = human is an **approval gate** (approve/edit/reject/respond), not a full peer member — humara "human = member" idea uspe graft karna padega.
- **AutoGen** = GroupChatManager (agent), pub-sub shared-topic group chat — closest OSS to "team=channel".
- **CrewAI** = hierarchical, manager is always an AI agent (no human manager).
- **Relevance AI** = process pipeline (not channel); one-way agent comms only.
- **Slack Agentforce** = channel=team + agent `@mention` "like a teammate" (closest product), but permissions **inherited from org RBAC** — no per-agent in-channel ownership tree (the gap we fill).

---

## 10. MVP scope

- **Phase 1:** ONE real research agent. Manager objective (research topic) deta → agent runs (search→synthesize) → findings channel mein.
- Objectives ek-ek karke; **research first, coding-type later.**
- Ownership/permission skeleton light but correct (agent #2/#3 add ho sakein).

---

## 11. Open items — VERIFIED (2026-07-12, web-researched, no guessing)

- [x] **`langgraph-checkpoint-mongodb`** — REAL & official (langchain-ai/langchain-mongodb, co-maint MongoDB). Latest **v0.4.0 (2026-05-12)**, Python ≥3.10. Separate install (not in langgraph 1.0 core).
  - `pip install -U "langgraph-checkpoint-mongodb>=0.4.0"`
  - Sync: `from langgraph.checkpoint.mongodb import MongoDBSaver`; Async: `from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver`
  - `checkpointer = MongoDBSaver(pymongo_client)` → `graph.compile(checkpointer=checkpointer)`. `from_conn_string(...)` auto-creates collections/indexes.
  - **Long-term store = separate pkg** `langgraph-store-mongodb` → `from langgraph.store.mongodb import MongoDBStore`. Plain KV works on any Mongo; **vector/semantic** store mode needs **Atlas Vector Search**.
  - Works on any Mongo reachable via pymongo/motor. **VERDICT: safe to build on.**
- [x] **deepagents vs plain LangGraph** → **plain LangGraph `create_agent`** (current name for `create_react_agent`; `from langchain.agents import create_agent`).
  - Reason: single search→synthesize ReAct loop; we already own orchestration + permission + subagent layer. deepagents' filesystem/subagents/HITL would **duplicate & fight** our layer. Both multi-provider. deepagents only worth it Phase-2+ if a single agent needs internal multi-step planning + parallel sub-delegation.
- [x] **Mongo hosting** → **Atlas M0** (cheapest reliable, permanently $0, zero ops).
  - M0 = real **3-node replica set** → **transactions work → LangGraph checkpointer works** ✅. 512MB, 500 conns, ~100 ops/s, 10GB/7d transfer, 1 M0 per project. Available in **GCP regions** (co-locate w/ Cloud Run). Auto-pause after 30d idle (resumable).
  - Networking: M0 has **no VPC peering** → public URI + IP allowlist `0.0.0.0/0` (rely on SCRAM+TLS), or VPC connector + Cloud NAT static IP.
  - Self-host e2-micro rejected: 1GB RAM, standalone (no txns unless manual single-node RS), real ops burden.
- [x] **WebSocket vs SSE on Cloud Run** → **SSE** (`EventSource`).
  - Push is one-way server→client (msgs/status/streamed output); client actions = plain POST. SSE = plain HTTP/1.1, native auto-reconnect (handles Cloud Run's **≤60-min request-timeout cutoff** cleanly). WS bidirectional wasted + proxy/reconnect complexity ("don't enable HTTP/2 e2e" for WS).
  - Gotchas: held-open conn keeps instance **active+billed**, 1 concurrency slot (max 1000/instance), **set min-instances ≥1** to avoid reconnect-storm cold starts; flush each event (no buffering).

---

## 12. Naming (settled)

- **Agent Deck** — "control deck" jahan se agents manage ho. Single clean concept, team+control feel.
- Rejected: Cohort-Guild (redundant, hyphen weak), Agent-Tech (too generic). Considered: Cohort, Guild, Roster, Order.

## 13. Member model reshape + permission freeze (2026-07-13)

- **Manager and member are ONE flat entity.** No stored `role`, no `manager_id`. Being a "manager" is contextual (owning a channel), never a field. → dropped `MemberRole`/`manager_id` from `Member`.
- **AgentConfig folded into Member** — agent run-settings live directly on the member (like the old project's user record): `name, color, provider, model, effort, trust, identity, thread_id, created_at, last_active_at`.
- **`thread_id` = the resumable session handle.** Claude keeps a `session_id`; LangGraph's equivalent is **`thread_id`** (the MongoDB-checkpointer key a conversation is stored under). So member carries `thread_id`, not a Claude-style `sessionId`.
- New enums: `ReasoningEffort {low,medium,high,xhigh,max}`, `TrustLevel {safe,full,readonly}` (trust semantics from the old terminal project).
- **Permission layer FROZEN** — `permissions.py` + `Permission`/`MemberRole` enums kept intact but paused; its tests `@skip`. Re-open later, refactored to derive "manager" from channel ownership (not a role field).
- Timestamps standardized via `clock.now_iso()` (ISO-8601 UTC) — one source, no format drift.

## 14. Phase 2 — research agent (built 2026-07-13)

Real APIs verified by introspection before coding (no guessing):
- `from langchain.agents import create_agent(model, tools, *, system_prompt, response_format, checkpointer, ...)` → `CompiledStateGraph`. Structured result at `result["structured_response"]` (AgentState has that key).
- `MongoDBSaver(client, db_name="checkpointing_db", ...)` — **connects on construction** (index setup), NOT lazy. `InMemorySaver` for keyless local.
- `ChatAnthropic(model_name=..., api_key=...)` (param is `model_name`, not `model`).
- Search: **DuckDuckGo via `ddgs`** = keyless real web search → only the LLM needs a key.

Pieces built:
- `agents/findings.py` — `ResearchFindings` (pydantic) = summary + evidence[claim/detail/source_url] + sources. Used as `response_format`.
- `tools/web_search.py` — `SearchProvider` protocol; `DuckDuckGoSearchProvider` (real), `StaticSearchProvider` (tests); `make_web_search_tool(provider)`.
- `memory/checkpointer.py` — `build_checkpointer(uri)` → Mongo or InMemory.
- `agents/research_agent.py` — `build_research_agent(model, search_provider, checkpointer)` + `make_researcher(agent)` (Researcher = objective+thread_id → findings; decouples runner from LangGraph).
- `runtime/session_runner.py` — `run_research_session(...)` owns PENDING→RUNNING→COMPLETED/FAILED.
- `config.py` — env → Settings + `build_chat_model`.

Tests: **16 pass, 13 skip** (12 permission-frozen + 1 real-LLM integration, skipped unless `ANTHROPIC_API_KEY`). Full graph compiles offline (CompiledStateGraph: model+tools nodes). To run for real: `export ANTHROPIC_API_KEY=...` (+ optional `MONGODB_URI`), then the integration test / a runner call.

---

## 15. "Manager" definition — one vocabulary (Ownership rename)

Tension found in `domain/models.py`: `Member` docstring says "no stored role, manager is contextual (owning a channel)", yet `Ownership` stored a `manager_id` — reintroducing "manager" as a stored thing, with two conflicting meanings (channel owner vs owner of an agent).

Decision — **"manager" is never a stored field; it's a derived label.** Two distinct, separately-named ownership facts:
- **channel owner** = `Channel.owner_id` — owns the whole team/channel.
- **agent owner** = `Ownership.owner_id` — controls one specific agent.

`Ownership.manager_id` → **renamed `owner_id`** (it's just a member, not a "manager type"). Kept the edge (not derived from channel) on purpose: the product's moat is *granular* ownership — one channel can have many humans each owning different agents, so a per-agent owner edge is required, not derivable from a single `Channel.owner_id`.

Derived rule (for permission unfreeze): a member is a "manager" IF it is some `Channel.owner_id` OR holds any `Ownership` edge. `MemberRole.MANAGER` stays reserved/derived — never persisted on `Member`. Permission engine: `CONTROL_AGENT` ⇐ `Ownership(owner_id=actor, agent_id=target)` exists; `CONTROL_CHANNEL` ⇐ `Channel.owner_id == actor`.

Applied now (low-risk, logic unchanged): `models.py`, `permissions.py` (frozen, ref updated to `edge.owner_id`), `tests/test_permissions.py`. Suite still **16 pass / 13 skip**.

Open (deferred with permission layer): `Session` has no timestamps (`created_at`/`started_at`/`completed_at`); `Member.created_at` auto vs `Message.created_at` required — document intent when unfreezing.

---

_Last updated: 2026-07-16 (Ownership.manager_id → owner_id; "manager" is derived, not stored)._
