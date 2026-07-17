# Agent MedIC — Self-Healing AI SRE Agent

[![SigNoz](https://img.shields.io/badge/Powered%20by-SigNoz-orange)](https://signoz.io)
[![OpenTelemetry](https://img.shields.io/badge/OTel-Instrumented-blue)](https://opentelemetry.io)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-50%20passing-brightgreen)](tests/)
[![Hackathon](https://img.shields.io/badge/Agents%20of%20SigNoz-2026-purple)](https://www.wemakedevs.org/hackathons/signoz)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)

**Track 01 — AI & Agent Observability** | Agents of SigNoz Hackathon 2026

**Team Enthusiast** — Rudra & Het Patel | Dr. Kiran and Pallavi Patel Global University

---

## Problem

AI agents are black boxes. When latency spikes, costs explode, or agents hallucinate, SRE teams are flying blind. Traditional observability tools don't understand AI workflows — and there's no feedback loop between detection, diagnosis, and auto-healing.

## Solution

Agent MedIC is a **self-observing AI SRE agent** that closes the loop:

1. **Watches** infrastructure via SigNoz alerts
2. **Investigates** using SigNoz MCP (traces + metrics + logs)
3. **Correlates** related alerts to infer root cause
4. **Diagnoses** root cause via local LLM (Ollama) with rule-based fallback
5. **Fixes** automatically (Docker restart, scale, clear cache)
6. **Logs** everything back into SigNoz as traces, metrics, and logs
7. **Traces itself** — every pipeline stage emits OpenTelemetry spans

---

## Architecture

```
SigNoz Alert → /webhook → Dedup → Rate-Limit → Correlator → Queue → Worker
                                                                  │
                          ┌───────────────────────────────────────┘
                          ▼
                    ┌─────────────┐
                    │  MCP Query  │──→ Traces, Metrics, Logs from SigNoz
                    ├─────────────┤
                    │  LLM Diag   │──→ Ollama (or rule-based fallback)
                    ├─────────────┤
                    │  Fix Exec   │──→ Docker restart / scale / clear cache
                    ├─────────────┤
                    │  Verify     │──→ Health check after fix
                    └─────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │  Log to SigNoz + DB  │──→ Traces, Metrics, WebSocket, Slack
              │  + WebSocket + Slack │
              └──────────────────────┘
```

**Agent emits its own OTel telemetry → SigNoz** — every pipeline stage, fix attempt, and LLM call is traced.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Observability | SigNoz (Foundry) + OpenTelemetry |
| Agent Backend | Python FastAPI |
| LLM | Ollama (llama3.2 — local, free) + rule-based fallback |
| MCP | SigNoz MCP Server |
| Auto-Fix | Docker SDK (restart, scale, cache clear) |
| Alert Correlation | Rule-based engine (10+ failure patterns) |
| Database | PostgreSQL |
| Agent Tracing | OpenTelemetry (self-instrumented) |
| Frontend | Vanilla HTML+JS+WebSocket |
| Notifications | Slack webhook |
| Deployment | Docker Compose (8 services) |

---

## Demo Scenarios (10 total)

| Scenario | Trigger | Agent Action | Expected Time |
|---|---|---|---|
| Redis Crash | Redis connection pool exhausted | Detect → Restart → Verify | ~26s |
| CPU Spike | CPU > 80% | Detect → Scale → Verify | ~35s |
| DB Timeout | PostgreSQL connection timeout | Detect → Restart → Verify | ~30s |
| Random 500s | Application errors | Detect → Log → Escalate | ~20s |
| Network Partition | DNS/connectivity failures | Detect → Restart → Verify | ~30s |
| Disk Full | Storage at 98% | Detect → Clear Cache → Verify | ~25s |
| Memory Leak | 45 MB/min growth | Detect → Restart → Verify | ~28s |
| Slow Queries | p99 latency at 12s | Detect → Scale → Verify | ~35s |
| TLS Cert Expiry | Certificate verification failed | Detect → Escalate | ~15s |
| OOM Kill | Container killed by OOM | Detect → Restart → Verify | ~25s |

Run automated demo: `bash scripts/demo.sh --simulated`

---

## SigNoz Dashboards

| Dashboard | Panels |
|---|---|
| **Pipeline Performance** | Incidents processed, fix success rate, stage latency (p95), LLM calls, queue depth, resolution rate |
| **Service Health** | Error rate by service, p95 latency by service, CPU/memory by service, health score |
| **Alert Correlation** | Correlation groups by root cause, inter-alert delay, top root causes |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/webhook` | Receive SigNoz alert |
| GET | `/health` | Health check |
| GET | `/incidents` | List incidents (paginated) |
| GET | `/incidents/{id}` | Incident detail |
| GET | `/incidents/stats/summary` | Aggregated stats |
| GET | `/metrics` | Agent metrics |
| POST | `/demo/trigger` | Trigger demo scenario |
| WS | `/ws/events` | Real-time events |

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

# 5. Run demo
bash scripts/demo.sh --simulated

# 6. Open dashboard
open http://localhost:3000
```

---

## Testing

```bash
pytest -v                          # All 50+ tests
pytest -m "not chaos" -v           # Skip destructive tests
pytest -m chaos -v                 # Chaos tests only
pytest -m "P0" -v                  # Critical tests only
```

---

## Team

| Member | Role |
|---|---|
| **Rudra** | Lead — Agent Core, MCP Integration, Pipeline, OTel Instrumentation |
| **Het Patel** | Developer — OTel Instrumentation, LLM Engine, Web UI |

**College:** Dr. Kiran and Pallavi Patel Global University

---

## Prizes Target

| Prize | Track | Status |
|---|---|---|
| Apple MacBook (per member) | Track 01 — AI & Agent Observability | 🎯 |
| LEGO Ferrari SF-24 | Side — Best Blog | 📝 |
| AWS Credits ($5K/$3K/$2K) | Cloud Sponsor | ☁️ |
| SigNoz Job Interview | Top blogs | 💼 |
| Exclusive Swag | Social media posts | 🎁 |

---

## License

MIT — See [LICENSE](LICENSE)
