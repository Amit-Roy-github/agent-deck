# AI Team / Channel — Prior Art vs. Your Concept

> Deep-research report. 22 sources fetched, 101 claims extracted, 25 adversarially verified (24 confirmed, 1 killed). State of the art as of **late 2025 / early 2026**.

---

## TL;DR (Hinglish)

- Tumhare concept ke **tukde** sab exist karte hain — par **exact combo** kisi ke paas nahi.
- Sabse bada gap: **first-class permission/ownership hierarchy** (manager owns agents, agent owns self) — koi framework isko primitive nahi banata.
- Dusra gap: **human aur agent ka same base "member" type** + **manager human ya agent dono ho sake** — har jagah human alag treat hota hai (approval gate), interchangeable nahi.
- **Team = Channel** unification sirf **Slack Agentforce** ke paas hai (agent ko `@mention` karke channel mein laao "just like a teammate"). Par Slack mein permissions **org se inherit** hoti hain — per-agent in-channel ownership tree nahi.
- **Closest starting point to build on:** conceptually **Slack's model** (channel = team, humans + agents side by side), architecturally **AutoGen** ya **LangGraph** (pub-sub / graph runtime). Neither gives you the ownership model — wo **tumhe khud** banana padega, aur wahi tumhara moat hai.

---

## Your concept (recap)

- **Team = Channel** — ek hi cheez, ek shared communication space.
- **Member** = base type; `kind ∈ {HUMAN, AGENT}`. Dono equal citizens.
- **Manager** — team chalata hai. Shuru mein human; baad mein agent bhi manager ban sakta.
- **Communication** — koi bhi member kisi se bhi (agent↔agent, agent↔human).
- **Permissions (first-class):** manager → controls whole channel + all owned agents. Agent → controls only itself.

---

## Comparison at a glance

| System | Team / Channel model | Manager can be human? | Human + agent = one member type? | Comms model | Permission / ownership |
|---|---|---|---|---|---|
| **LangGraph supervisor** | Graph of nodes | ❌ supervisor is always an LLM node | ❌ human = interrupt/approval gate | Central hub; workers can't talk laterally, tool-based handoffs | Code-defined; no in-channel ownership tree |
| **LangGraph (swarm/network)** | Graph topology | ❌ | ❌ | Direct agent↔agent via `Command`/handoff | Code-defined |
| **CrewAI (hierarchical)** | Crew | ❌ manager is always an AI agent (`manager_llm`/`manager_agent`) | ❌ | Manager delegates to workers | Role/goal per agent; no human-manager |
| **AutoGen GroupChatManager** | Shared pub-sub **topic** (team≈channel) | ❌ manager is an agent; human = separate `UserAgent` | ⚠️ partial (UserAgent exists but is distinct) | Pub-sub: manager `RequestToSpeak` → agent publishes `GroupChatMessage` to shared topic | Turn-control only; no ownership hierarchy |
| **Relevance AI "Workforce"** | Visual-canvas **process pipeline** (not a channel) | ❌ | ❌ humans = approval/escalation gates | **One-way** handoffs along drawn edges; bidirectional "not yet available" | Per-edge approval config; step-ownership, not member-ownership |
| **Slack + Agentforce** | **Channel = team** ✅ (closest) | ✅ humans are real channel members; agents `@mentioned` "like a teammate" | ⚠️ agents modeled *as* teammates, but bots ≠ same base type | In-channel `@mention`; **Slackbot MCP client** = hub-and-spoke router | **Inherited** from org/OAuth/admin — **NOT** a per-agent in-channel ownership tree |
| **Salesforce Agentforce (core)** | Persona/role scoped | n/a (runtime user context) | ❌ | Orchestrated | Persona → permission-set group; agent runs as its own "Agent User" with own scope |

Legend: ✅ present · ⚠️ partial · ❌ absent

---

## Per-system detail (verified)

### LangGraph — supervisor pattern
- **Manager = LLM, never human.** `create_supervisor(model=...)` builds a central **supervisor agent** that "controls all communication flow and task delegation." No human-supervisor capability in this library.
- **Comms:** workers **cannot** talk directly — "all communication must flow through the supervisor" via tool-based handoffs (`create_handoff_tool`, `transfer_to_<agent>`).
- **Note:** broader LangGraph *can* build **swarm/network** topologies where agents hand off directly to each other (`Command`) — a different architecture from the supervisor package.

### LangGraph / deepagents — human-in-the-loop
- **HITL is first-class** (a stated design pillar): `interrupt()` pauses the graph mid-run, marks the thread `interrupted`, resumes via `Command(resume=...)`.
- `interrupt_on` inserts `HumanInTheLoopMiddleware`; on a tool call the human can **Approve / Edit / Reject / Respond** — "one decision per action, in order."
- **But:** the human is an **out-of-band approval gate keyed to tool calls**, not a symmetric conversational member. Docs mention **no** manager/supervisor/delegation role for the human. → Not your unified-member model.

### CrewAI — hierarchical process
- **Manager is always an AI agent.** Either `manager_llm` (auto-creates a manager agent) or `manager_agent` (custom agent you define with role/goal). The manager delegates to workers and validates outputs.
- **No human-manager concept** in hierarchical mode.

### AutoGen — GroupChatManager
- **Closest to "team = channel" among OSS frameworks.** Agents "share a common thread of messages: they all subscribe and publish to the **same topic**" (a pub-sub channel). Sequential — "only one agent works at a time."
- **Manager = agent** (`class GroupChatManager(RoutedAgent)`), selects next speaker via LLM. Human takes the separate `UserAgent` role — so humans exist but as a **distinct** role, not a unified base member.
- **Comms:** manager publishes `RequestToSpeak` to the chosen agent → agent publishes `GroupChatMessage` back to the shared topic. Event-driven pub-sub.

### Relevance AI — "Workforce"
- **Not a channel — a process pipeline.** "Coordinated teams of agents that own a process end to end… each agent owns a step, hands off context." Built on a **visual canvas** of drawn connections.
- **Comms is one-way only:** docs state "only one-way communication is supported between agents. Bidirectional… is **not yet available**." Two modes: "AI Connection" (conditional handoff) and "Next Step" (forced). Always along predefined edges — **no** free-form any-to-any messaging.
- **Humans = gates, not members:** "Drag in agents, tools, and **approvals** in a flow." Approvals configured **per-edge**; humans are escalation *targets*, never step-owning peers.

### Slack + Agentforce
- **Team = Channel, natively** — and agents are literally brought into a channel/DM: "@mention an agent… **just like any other teammate**." "Agents operate in the same channels where teams already work… ask questions and trigger actions." An **agent directory** lists agents by skill.
- **Vision:** Slack explicitly targets "a future where humans and all agents can work securely **side by side**." This is the closest anyone comes to your human+agent unified channel.
- **Two comms modes:**
  1. **In-channel peer** — `@mention` agents in the flow of work.
  2. **Slackbot as MCP client** (GA ~March 2026) — a **hub-and-spoke router**: User → Slackbot → Agentforce → specialized agents. Central orchestrator, *not* peers messaging each other.
- **Permissions — the key gap for you:** agents are **"governed by default, inheriting every permission your organization has already established."** Authority = per-user **OAuth consent** + org/admin config. There is **NO first-class per-agent ownership hierarchy inside a channel** — Slack's own guidance says admins must *impose* an ownership model as an operational best practice, because there's no built-in primitive for it.
- **Refuted claim (killed in verify):** "Agentforce agents have no independent permission scope, they only borrow the prompting user's." **False** — each Agentforce agent runs as a dedicated **"Agent User"** with its own permission set. Employee-context filtering sits *on top* of that; it doesn't replace it.

---

## What's genuinely novel / underserved in your concept

1. **Permission-driven ownership hierarchy as a first-class primitive** — "manager owns these agents; an agent owns only itself."
   → **No framework models this.** Slack inherits from org RBAC; AutoGen/CrewAI/LangGraph only encode *turn/delegation control*, not *ownership*. **This is your strongest differentiator.**

2. **Manager that can be human OR agent, interchangeably** — same slot, either kind.
   → OSS managers are **always LLM agents** (LangGraph supervisor, CrewAI, AutoGen). Slack managers are humans via org roles. Nobody makes the manager role **kind-agnostic and swappable**.

3. **Human and agent as the same base "member" type** — full peer, not a gate.
   → Everyone treats the human as a **HITL approval gate** (LangGraph, Relevance AI) or a **distinct role** (AutoGen `UserAgent`). Slack gets closest ("agent as teammate") but agents are still apps/bots, not the same base entity as a human.

4. **Team = Channel unification** — one object, not "a pipeline" + "a chat" bolted together.
   → AutoGen (shared topic) and Slack (channel) partially have this. Relevance AI, CrewAI, LangGraph do **not** — their "team" is an execution graph/pipeline, separate from any conversation surface.

5. **Human-in-the-loop by default** — because a human is just a member, oversight is native, not a special `interrupt`.
   → Everyone else bolts HITL on as a separate mechanism.

---

## Closest starting point to build on

- **Product/mental model:** **Slack Agentforce** — channel = team, humans + agents side by side, `@mention` to pull an agent in. Copy this UX; then add the layer Slack lacks (in-channel ownership).
- **Runtime engine (pick one):**
  - **AutoGen** — its pub-sub **shared-topic** group chat is the cleanest match for "channel where every member subscribes/publishes." Manager-selects-speaker maps to your manager. You'd extend it with: unified member type, human-or-agent manager, and the ownership permission layer.
  - **LangGraph** — if you want explicit graph control + **built-in HITL** (`interrupt`) and the option of both hub (supervisor) and peer (swarm) topologies. More plumbing, more control.
- **The part you must build yourself (and your moat):** the **ownership/permission model** — `Member{kind, role, managerId}`, `Channel{ownerId, memberIds[]}`, and a permission enum (`CONTROL_SELF | CONTROL_AGENT | CONTROL_CHANNEL | SEND_MESSAGE`). No existing system hands you this; that's precisely the underserved space.

**Recommendation:** Slack model for UX + AutoGen (or LangGraph) as the message runtime + your own ownership/permission layer on top.

---

## Caveats

- Fast-moving space — Slack shipped ~30 AI features around **March 2026**; framework APIs (LangGraph supervisor, deepagents, Microsoft Agent Framework 1.0) churn fast. Verify exact APIs before building.
- **Microsoft Agent Framework** (merges AutoGen + Semantic Kernel), **Magentic-One** (orchestrator + task-ledger), **OpenAI Agents SDK / Swarm** (handoff-based), and the **A2A protocol** (cross-vendor agent-to-agent interop) appeared as sources but weren't deeply claim-verified in this run — worth a focused look if you go the standards/interop route.
- Vendor pages are marketing; where it mattered (esp. Slack/Agentforce permission claims) findings were cross-checked against neutral technical docs.

---

## Sources (primary, verified)

- LangGraph supervisor — `github.com/langchain-ai/langgraph-supervisor-py`, `reference.langchain.com/python/langgraph-supervisor`
- LangGraph HITL — `langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt`
- deepagents HITL — `docs.langchain.com/oss/python/deepagents/human-in-the-loop`
- CrewAI hierarchical — `docs.crewai.com/.../custom-manager-agent`, `docs.crewai.com/en/learn/hierarchical-process`
- AutoGen group chat — `microsoft.github.io/autogen/stable/.../design-patterns/group-chat.html`
- Magentic-One — `microsoft.github.io/autogen/stable/.../magentic-one.html`
- Microsoft Agent Framework 1.0 — `devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/`
- A2A protocol — `a2a-protocol.org/latest/`
- Relevance AI Workforce — `relevanceai.com/workforce`, `relevanceai.com/docs/.../workforces`, `.../agent-to-agent-configuration`, `.../approvals-and-escalations`
- Slack agents — `slack.com/blog/news/turn-agents-into-teammates-with-slack`, `slack.com/blog/news/ai-for-employees-agentforce-slack`, `slack.com/blog/news/agent-orchestration`, `docs.slack.dev/ai/agent-governance`
- Salesforce Agentforce — `salesforce.com/news/stories/new-collaborative-workforce-humans-agents/`, `salesforce.com/slack/slackbot/agent-orchestration/`
