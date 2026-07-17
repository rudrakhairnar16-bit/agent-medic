# Agent MedIC — Self-Healing AI SRE Agent

**Track 01 — AI & Agent Observability** | Agents of SigNoz Hackathon 2026

Team Enthusiast — Rudra & Het Patel | Dr. Kiran and Pallavi Patel Global University

---

## Problem

AI agents are black boxes. When latency spikes, costs explode, or agents hallucinate, SRE teams are flying blind. Traditional observability tools don't understand AI workflows.

## Solution

Agent MedIC is an AI SRE agent that:
1. **Watches** infrastructure via SigNoz alerts
2. **Investigates** using SigNoz MCP (traces + metrics + logs)
3. **Diagnoses** root cause via local LLM (Ollama)
4. **Fixes** automatically (Docker restart, scale, etc.)
5. **Logs** everything back into SigNoz

## Quick Start

```bash
signoz install
docker compose up -d
open http://localhost:3000
```

## Tech Stack

| Layer | Technology |
|---|---|
| Observability | SigNoz (Foundry) + OpenTelemetry |
| Agent Backend | Python FastAPI + LangGraph |
| LLM | Ollama (llama3.2 — local, free) |
| MCP | SigNoz MCP Server |
| Auto-Fix | Docker SDK |
| Database | PostgreSQL |
| Frontend | Vanilla HTML+JS+WebSocket |

## Demo Scenarios

- Redis crash → auto-restart
- CPU spike → auto-scale
- DB timeout → auto-restart
- Random 500s → detect + log

## Prizes Target

- Apple MacBook (per member) — Track 01
- LEGO Ferrari SF-24 — Best Blog
- AWS Credits — Cloud Sponsor
