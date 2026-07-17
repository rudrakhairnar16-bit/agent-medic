# Agent MedIC — Self-Healing AI SRE Agent

[![SigNoz](https://img.shields.io/badge/Powered%20by-SigNoz-orange)](https://signoz.io)
[![OpenTelemetry](https://img.shields.io/badge/OTel-Instrumented-blue)](https://opentelemetry.io)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-26%20passing-brightgreen)](tests/)

**Track 01 — AI & Agent Observability** | Agents of SigNoz Hackathon 2026

**Team Enthusiast** — Rudra & Het Patel | Dr. Kiran and Pallavi Patel Global University

---

## Problem

AI agents are black boxes. When latency spikes, costs explode, or agents hallucinate, SRE teams are flying blind. Traditional observability tools don't understand AI workflows.

## Solution

Agent MedIC is an AI SRE agent that:

1. **Watches** infrastructure via SigNoz alerts
2. **Investigates** using SigNoz MCP (traces + metrics + logs)
3. **Diagnoses** root cause via local LLM (Ollama)
4. **Fixes** automatically (Docker restart, scale, clear cache)
5. **Logs** everything back into SigNoz

---

## Architecture

```
User → SigNoz (alerts + MCP) → Agent MedIC → Ollama (diagnosis) → Docker (fix) → SigNoz (log)
```

[Full Architecture](Agent_MedIC_Architecture.md)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Observability | SigNoz (Foundry) + OpenTelemetry |
| Agent Backend | Python FastAPI + LangGraph |
| LLM | Ollama (llama3.2 — local, free) |
| MCP | SigNoz MCP Server (stdio/HTTP) |
| Auto-Fix | Docker SDK (restart, scale, cache clear) |
| Database | PostgreSQL |
| Frontend | Vanilla HTML+JS+WebSocket |
| Deployment | Docker Compose |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/rudrakhairnar16-bit/agent-medic.git
cd agent-medic

# 2. Install SigNoz via Foundry
signoz install

# 3. Start everything
docker compose up -d

# 4. Pull LLM model
docker exec -it ollama ollama pull llama3.2

# 5. Open dashboard
open http://localhost:3000
```

---

## Project Structure

```
agent-medic/
├── README.md                   # This file
├── casting.yaml                # Foundry config (MANDATORY)
├── casting.yaml.lock           # Foundry lock (MANDATORY)
├── docker-compose.yml          # 7 services
├── pytest.ini                  # Test configuration
├── demo-script.md              # Demo video script
│
├── sample-app/                 # OTel-instrumented buggy microservice
│   ├── app.py                  # FastAPI with 4 bug triggers
│   ├── instrument.py           # OpenTelemetry setup
│   └── bugs/                   # high_cpu, memory_leak, db_timeout, random_errors
│
├── agent_medic/                # Core agent (Python package)
│   ├── main.py                 # FastAPI server entrypoint
│   ├── config.py               # Environment configuration
│   ├── worker.py               # Background pipeline worker
│   ├── pipeline/               # Queue, dedup, rate limiter
│   ├── listeners/              # SigNoz webhook receiver
│   ├── mcp/                    # SigNoz MCP client + fallback API
│   ├── llm/                    # Ollama + LangGraph + rule-based fallback
│   ├── fix/                    # Docker restart/scale/cache executor
│   ├── logging/                # Incident logger, notifier, metrics
│   ├── db/                     # PostgreSQL models + repository
│   └── api/                    # REST + WebSocket routes
│
├── web-ui/                     # Agent dashboard (HTML+JS+WS)
├── scripts/                    # setup, seed-data, load-test, demo
├── tests/                      # 26 tests (pytest)
├── Agent_MedIC_Report.md       # Project report
└── Agent_MedIC_Architecture.md # Full architecture
```

---

## Demo Scenarios

| Scenario | Trigger | Agent Action | Expected Time |
|---|---|---|---|
| Redis Crash | `docker stop redis` | Detect → Restart → Verify | ~26s |
| CPU Spike | `curl /trigger/high-cpu` | Detect → Scale → Verify | ~35s |
| DB Timeout | `curl /trigger/db-timeout` | Detect → Restart → Verify | ~30s |
| Random 500s | `curl /trigger/random-500` | Detect → Log → Escalate | ~20s |

Run automated demo: `bash scripts/demo.sh`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/webhook` | Receive SigNoz alert |
| GET | `/health` | Health check |
| GET | `/incidents` | List incidents (paginated) |
| GET | `/incidents/{id}` | Incident detail |
| GET | `/metrics` | Agent metrics |
| WS | `/ws/events` | Real-time events |

---

## Testing

```bash
pytest -v                    # All tests
pytest -m P0 -v              # Critical tests only
pytest -m "not chaos" -v     # Skip destructive tests
```

---

## Team

| Member | Role |
|---|---|
| **Rudra** | Lead — Agent Core, MCP Integration, Pipeline |
| **Het Patel** | Developer — OTel Instrumentation, LLM Engine, Web UI |

**College:** Dr. Kiran and Pallavi Patel Global University

---

## Prizes Target

| Prize | Track | Status |
|---|---|---|
| Apple MacBook (per member) | Track 01 — AI & Agent Observability | 🎯 |
| LEGO Ferrari SF-24 | Side — Best Blog | 📝 |
| AWS Credits ($5K/$3K/$2K) | Cloud Sponsor | ☁️ |

---

## License

MIT — See [LICENSE](LICENSE)
