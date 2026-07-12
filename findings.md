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

## 11. Open items to verify BEFORE coding (no-guessing rule)

- [ ] `langgraph-checkpoint-mongodb` — exact package name, install, API, maintained? version? (load-bearing — poori DB decision)
- [ ] **deepagents vs plain LangGraph** — research agent ka base konsa
- [ ] **MongoDB Atlas free tier** vs GCP-native — cheapest Cloud Run + Mongo path
- [ ] **WebSocket vs SSE on Cloud Run** — channel realtime ke liye (limits check)

---

## 12. Naming (settled)

- **Agent Deck** — "control deck" jahan se agents manage ho. Single clean concept, team+control feel.
- Rejected: Cohort-Guild (redundant, hyphen weak), Agent-Tech (too generic). Considered: Cohort, Guild, Roster, Order.

---

_Last updated: 2026-07-12 (design phase locked)._
