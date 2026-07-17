# AGENT MEDIC — Repo Plan for Perfect Submission

**Repo:** https://github.com/rudrakhairnar16-bit/agent-medic  
**Visibility:** Public  
**Description:** Self-healing AI SRE Agent powered by SigNoz MCP — Agents of SigNoz Hackathon 2026 by Team Enthusiast

---

## 1. README Template

```markdown
# Agent MedIC — Self-Healing AI SRE Agent

[Track 01 — AI & Agent Observability] | Agents of SigNoz Hackathon 2026
Team: Enthusiast | Rudra & Het Patel | Dr. Kiran and Pallavi Patel Global University

Problem: AI agents are black boxes. When latency spikes or agents hallucinate, SRE teams are flying blind.

Solution: Agent MedIC watches via SigNoz → investigates via MCP → diagnoses via Ollama → fixes via Docker → logs everything back.

Prizes Target:
- Apple MacBook (per member) — Track 01
- LEGO Ferrari SF-24 — Best Blog side track
- AWS Credits — Cloud sponsor

Quick Start:
  signoz install
  docker compose up -d
  open http://localhost:3000

Demo Scenarios: Redis crash, CPU spike, DB timeout, Random 500s
```

---

## 2. Submission Checklist

| Item | Status |
|---|---|
| casting.yaml + casting.yaml.lock | ⬜ |
| All source code | ⬜ |
| README with screenshots + links | ⬜ |
| Demo video (3 min) | ⬜ |
| Blog post (Dev.to) | ⬜ |
| Social posts (@wemakedevs @SigNozHQ) | ⬜ |
| All P0 tests passing | ⬜ |
| Final git push | ⬜ |

---

## 3. .gitignore

```
__pycache__/ *.py[cod] venv/ .venv/
.env .env.local .vscode/ .idea/
docker-data/ *.log *.pdf .DS_Store
```

---

## 4. Files Structure

```
agent-medic/
├── README.md
├── LICENSE (MIT)
├── .gitignore
├── .env.example
├── casting.yaml          (MANDATORY)
├── casting.yaml.lock     (MANDATORY)
├── docker-compose.yml
├── sample-app/           (OTel microservice + 4 bugs)
├── agent-medic/          (8 subpackages: pipeline, listeners, mcp, llm, fix, logging, db, api)
├── web-ui/               (index.html + style.css + app.js)
├── scripts/              (load-test, seed-data, demo)
└── tests/                (50 tests)
```

---

## 5. Push Commands

```bash
git init
git add .
git commit -m "init: Agent MedIC — Self-Healing AI SRE Agent"
git remote add origin https://github.com/rudrakhairnar16-bit/agent-medic.git
git branch -M main
git push -u origin main
```

---

*Repo plan for Agents of SigNoz Hackathon 2026*
*Team Enthusiast — Rudra & Het Patel*
