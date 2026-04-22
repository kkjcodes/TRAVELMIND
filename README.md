# TravelMind

**An agentic AI platform demonstrating production-grade multi-agent orchestration, human-in-the-loop safety gates, and Claude API tool use — built as a portfolio project for roles at the intersection of backend systems and AI.**

---

## What This Is

TravelMind is a multi-agent travel intelligence platform. It takes a traveler profile and — through a coordinated pipeline of specialized AI agents — produces personalized destination recommendations, trip cost estimates, and targeted marketing campaigns.

The point isn't travel. The point is the architecture:

- **How do you structure a system where multiple AI agents collaborate without stepping on each other?**
- **How do you build a safety gate that stops an AI from taking a high-value action without human sign-off?**
- **How do you wire Claude's tool-use API into a real agentic loop — not just a single prompt, but a full think → call tool → observe result → continue cycle?**

TravelMind answers those questions with working code, a full test suite, and a Streamlit UI you can run locally.

---

## Architecture

```
User (Streamlit UI)
        │
        ▼
┌─────────────────────┐
│    Orchestrator     │  ← Coordinates all agents, owns the request lifecycle
└──────┬──────────────┘
       │
       ├──▶ Profile Agent     → Analyzes traveler segment, loyalty tier, preferences
       │                         Uses: get_traveler_profile, compute_segment_score
       │
       ├──▶ Discovery Agent   → Searches destinations, hotels, estimates trip cost
       │                         Uses: search_destinations, get_hotel_recommendations,
       │                               estimate_trip_cost
       │
       └──▶ Marketing Agent   → Generates campaigns, scores conversion likelihood
                                 Uses: generate_email_campaign, score_campaign_likelihood,
                                       submit_for_approval  ← HITL gate lives here
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │  Approval Queue  │  (SQLite-backed)
                                    │  Human reviews   │
                                    │  approve/reject  │
                                    └──────────────────┘
```

Each agent runs an independent Claude agentic loop: `tool_use` → execute tool locally → feed result back → repeat until `end_turn`. Agents share no state — the Orchestrator passes context explicitly as structured prompts.

---

## Key Engineering Decisions

**1. Tool-use agentic loop (not single-shot prompting)**

Each agent calls Claude via `messages.create()`, inspects `stop_reason`, and loops:

```python
while True:
    response = client.messages.create(model=MODEL, tools=self.tools, messages=messages)

    if response.stop_reason == "end_turn":
        return self._extract_text(response.content), total_tokens

    if response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input, customer_profile)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, ...})

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

This is the same loop pattern used in production agentic systems — not a wrapper, not a framework abstraction.

**2. Prompt caching on system prompts**

All system prompts are marked `cache_control: {type: "ephemeral"}`, which tells Anthropic's API to cache the prompt prefix. Repeated agent calls within a session hit the cache, reducing latency and cost:

```python
system=[{
    "type": "text",
    "text": self.system_prompt,
    "cache_control": {"type": "ephemeral"},
}]
```

**3. Human-in-the-Loop (HITL) safety gate**

The Marketing Agent's system prompt enforces a hard rule: if `estimated_value > $500` OR `action_type` is in `{booking_confirmation, bulk_marketing_send}`, Claude must call `submit_for_approval` before proceeding. The threshold and action types are configurable in `config.py`.

This is the same pattern used in production AI systems where automated actions need a review layer — a circuit breaker for agent behavior.

**4. SQLite as a lightweight operational store**

Three tables: `customers` (seed data for 5 traveler personas), `hitl_requests` (approval queue state), `agent_runs` (observability log). The database path is environment-variable-driven so tests use isolated temp databases without interfering with each other or the dev DB.

---

## Traveler Seed Data

Five pre-seeded customer personas for immediate demo use:

| Customer | Segment | Loyalty | Budget |
|---|---|---|---|
| Alexandra Chen | Luxury | Platinum | $5K–$20K |
| Marcus Williams | Business | Gold | $2K–$8K |
| The Rodriguez Family | Family | Silver | $3K–$10K |
| Jordan Kim | Adventure | Silver | $2.5K–$7K |
| Patricia Moore | Occasional | Standard | $1.5K–$4K |

---

## UI — Four Operational Tabs

| Tab | What It Does |
|---|---|
| **Trip Planner** | Select a traveler → Profile Agent + Discovery Agent → ranked recommendations |
| **Proactive Scan** | Full pipeline: profile + discovery + campaign generation with HITL gate |
| **Approval Queue** | Review, approve, or reject pending high-value agent actions |
| **Marketing Studio** | Single-customer or bulk campaign generation |

---

## Project Structure

```
TravelMind/
├── app.py                        # Streamlit UI — 4 operational tabs
├── requirements.txt
├── pytest.ini
├── travel_mind/
│   ├── config.py                 # Model, HITL thresholds, DB path
│   ├── models.py                 # TravelerProfile, HITLRequest, AgentResult dataclasses
│   ├── database.py               # SQLite schema, CRUD, seed data, agent run logging
│   ├── tools.py                  # 13 tool definitions + simulated executors
│   └── agents/
│       ├── base.py               # Agentic loop: tool_use → execute → end_turn
│       ├── orchestrator.py       # Coordinates sub-agents for plan_trip, proactive_scan
│       ├── profile_agent.py      # Traveler segmentation and personalization scoring
│       ├── discovery_agent.py    # Destination search, hotel recommendations, cost estimates
│       └── marketing_agent.py    # Campaign generation with HITL enforcement
└── tests/
    ├── conftest.py               # Isolated temp DB per test run
    ├── test_models.py            # HITL threshold logic, model serialization
    ├── test_database.py          # Customer CRUD, approval queue state transitions
    ├── test_tools.py             # Tool executor correctness
    └── test_agents.py            # Agent behavior with mocked Claude API
```

**70 tests, all passing.** Agents are tested with mocked Claude responses — no live API calls needed to run the test suite.

---

## Setup

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd TravelMind
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your Anthropic API key

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

Get an API key at [console.anthropic.com](https://console.anthropic.com). A few dollars in credits is enough for extensive testing with `claude-sonnet-4-6`.

### 5. Run the app

```bash
streamlit run app.py
```

### 6. Run the test suite

```bash
pytest
```

No API key needed — agents are mocked in tests.

---

## Configuration

All tuneable settings are in `travel_mind/config.py`:

```python
MODEL = "claude-sonnet-4-6"
HITL_VALUE_THRESHOLD = 500.0                              # USD — actions above this go to approval queue
HITL_ACTION_TYPES = {"booking_confirmation", "bulk_marketing_send"}   # Always require approval
MAX_TOKENS = 4096
DB_PATH = "travelmind.db"                                 # Override with TRAVELMIND_DB env var
```

---

## Troubleshooting

**`anthropic.BadRequestError: credit balance too low`**
→ Add credits at [console.anthropic.com](https://console.anthropic.com) → Billing. Verify the key in your shell matches the account with credits: `echo $ANTHROPIC_API_KEY`.

**App starts but agents return nothing**
→ Some tool executors are intentionally simulated — the architecture and orchestration patterns are real, the downstream data (hotel prices, destinations) is static catalog data.

**Database not found**
→ The DB is created automatically on first startup. If you set `TRAVELMIND_DB`, make sure the directory exists.

---

## Roadmap

- Replace simulated tool executors with live APIs (Amadeus for flights, Google Places for hotels)
- Stream agent responses token-by-token to the UI via `client.messages.stream()`
- Add async job queue (Celery or ARQ) for long-running proactive scan jobs
- Role-based approval controls and a full audit dashboard
- Integration tests for end-to-end UI workflows

---

## Tech Stack

`Python` · `Anthropic Claude API` · `claude-sonnet-4-6` · `Tool Use` · `Prompt Caching` · `Streamlit` · `SQLite` · `pytest`
