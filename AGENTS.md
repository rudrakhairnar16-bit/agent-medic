# Agent MedIC — Project Knowledge

## Overview
Self-healing AI SRE Agent for SigNoz Hackathon Track 01 (AI & Agent Observability).
Team Enthusiast — Rudra Khaire (lead) + Het Patel. Dr. Kiran and Pallavi Patel Global University.

## Stack
- **Backend:** Python FastAPI + LangGraph + SQLAlchemy (PostgreSQL)
- **LLM:** Ollama (local, llama3.2) with rule-based fallback
- **Observability:** SigNoz via MCP protocol + HTTP fallback
- **Fixes:** Docker SDK (restart/scale/clear-cache)
- **Frontend:** Vanilla HTML/JS/WebSocket → nginx
- **Orchestration:** Docker Compose (7 services)

## Architecture
```
SigNoz Alert → /webhook → Dedup → Rate-Limit → Queue → Worker
  → MCP queries (traces/metrics/logs)
  → LLM diagnosis (Ollama / fallback)
  → Fix execution (Docker restart/scale/cache)
  → Verification → Log to DB + WebSocket + SigNoz + Slack
```

## Project Structure
```
Track_1/
├── agent_medic/          # Core application package
│   ├── main.py           # FastAPI entrypoint + startup
│   ├── config.py         # Config from env vars (DEMO_MODE flag)
│   ├── worker.py         # Background pipeline worker
│   ├── api/
│   │   ├── routes.py     # REST endpoints (health, incidents, metrics, demo/trigger)
│   │   ├── schemas.py    # Pydantic models
│   │   └── websocket.py  # WebSocket /ws/events
│   ├── db/
│   │   ├── models.py     # SQLAlchemy Incident table
│   │   └── repository.py # CRUD operations
│   ├── pipeline/
│   │   ├── queue.py      # Async incident queue
│   │   ├── dedup.py      # Deduplication (time-window)
│   │   └── rate_limiter.py # Rate limiting
│   ├── mcp/
│   │   ├── client.py     # MCP stdio/HTTP + SigNozApi fallback
│   │   ├── queries.py    # 5 query templates
│   │   └── response_parser.py
│   ├── llm/
│   │   ├── engine.py     # OllamaClient + RuleBasedFallback
│   │   ├── prompts.py    # SYSTEM_PROMPT + build_diagnosis_prompt
│   │   ├── context_builder.py
│   │   └── response_parser.py
│   ├── fix/
│   │   ├── actions.py    # Action definitions + validation
│   │   ├── docker_client.py  # Lazy Docker init (graceful fail)
│   │   ├── executor.py   # Async execute + verify
│   │   └── health_verifier.py
│   ├── incidents/
│   │   ├── incident_logger.py  # DB + WebSocket + Slack + SigNoz
│   │   ├── metrics_collector.py
│   │   └── notifier.py
│   └── simulated/        # Demo mode (NEW)
│       ├── __init__.py   # SimulatedMCPClient, SimulatedFixExecutor, SimulatedOllamaClient
│       └── data.py       # 4 pre-built scenarios
├── sample-app/           # OTel-instrumented microservice
│   ├── app.py            # FastAPI with 4 bug triggers
│   ├── instrument.py     # OTel SDK init
│   ├── bugs/             # Bug modules (high-cpu, memory-leak, etc.)
│   └── Dockerfile
├── web-ui/               # Frontend (nginx)
│   ├── index.html        # Stats cards + live event list
│   ├── app.js            # WebSocket connect + auto-refresh
│   ├── style.css         # Dark theme
│   └── Dockerfile
├── scripts/
│   ├── setup.sh          # Environment setup guide
│   ├── seed-data.py      # Seeds all 4 scenarios (--demo flag)
│   ├── demo.sh           # Automated demo sequence
│   ├── load-test.sh      # Locust load test
│   └── seed-data.sh      # Manual seed guide
├── tests/                # 27 tests (P0=critical)
│   ├── conftest.py       # Path setup
│   ├── test_mcp_client.py
│   ├── test_llm_engine.py
│   ├── test_fix_executor.py
│   ├── test_pipeline.py
│   └── test_integration.py
├── docker-compose.yml    # 7 services
├── casting.yaml          # SigNoz Foundry config (MANDATORY)
├── .env.example
└── pytest.ini
```

## Demo Mode
Set `DEMO_MODE=true` to run without real services. Simulated clients provide:
- 4 pre-built scenarios (redis_crash, cpu_spike, db_timeout, random_500s)
- Mock MCP data (traces, metrics, logs)
- Fake fix execution (always succeeds)
- Trigger via `POST /demo/trigger?scenario=redis_crash`

## Key Commands
```bash
# Run directly (with simulated clients)
cd Track_1
$env:DEMO_MODE="true"
python agent_medic/main.py

# Run tests (must be from Track_1 directory)
python -m pytest tests/ -v

# Run with uvicorn
uvicorn agent_medic.main:app --host 0.0.0.0 --port 8000
```

## Testing Strategy
- **P0 (critical):** Core pipeline — queue, dedup, rate-limiter, integration tests (20 tests)
- **P1 (important):** MCP client, LLM engine, fix executor (12 tests)
- **P2 (nice-to-have):** Simulated mode, stress tests, end-to-end

All tests must pass before commit. Run `python -m pytest tests/ -v` to verify.

## Git Convention
- Commits: `feat:` / `fix:` / `refactor:` / `test:` / `docs:` / `chore:`
- Immediate commit after each batch of changes
- Push to `origin/main`
