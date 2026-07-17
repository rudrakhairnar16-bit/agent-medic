# Agent MedIC — Demo Script (3 minutes)

---

## Scene 1: Overview (0:00 - 0:30)

**Visual:** Web UI dashboard showing "0 Incidents — Healthy"

**Narrator:** "Meet Agent MedIC — a self-healing AI SRE agent powered by SigNoz. It watches your infrastructure, auto-debugs failures, and heals them. Let's see it in action."

---

## Scene 2: Redis Crash (0:30 - 1:00)

**Action:** Click "Trigger Redis Crash" on sample-app

**Visual:** SigNoz alert fires → Webhook received → Agent starts investigating

**Narrator:** "We triggered a Redis crash. SigNoz detects the error rate spike and fires a critical alert. Agent MedIC receives it via webhook."

---

## Scene 3: Investigation (1:00 - 1:30)

**Visual:** Agent dashboard showing: "Querying traces... Querying metrics... Querying logs..."

**Narrator:** "The agent queries SigNoz via MCP — traces show connection failures, metrics show Redis errors, logs confirm the outage. All telemetry is analyzed by Ollama LLM running locally."

**Visual:** LLM diagnosis popup: "Root cause: Redis connection pool exhausted (confidence: 0.92)"

---

## Scene 4: Auto-Fix (1:30 - 2:00)

**Visual:** Agent dashboard: "Executing fix: restart_container(redis)" → Docker restart animation

**Narrator:** "Diagnosis complete. Agent MedIC executes the fix via Docker SDK — restarting the Redis container. It then verifies by querying SigNoz again."

**Visual:** "Error rate: 0% → Verified ✅"

---

## Scene 5: Resolution (2:00 - 2:30)

**Visual:** Web UI updates: "Incident #1 — Resolved in 26 seconds"

**Narrator:** "Incident resolved in 26 seconds. Everything is logged back into SigNoz — the alert is resolved, a custom log is pushed with the incident data, and the Web UI updates in real-time."

**Visual:** SigNoz dashboard showing resolved alert + custom incident log

---

## Scene 6: Summary (2:30 - 3:00)

**Visual:** Architecture diagram overlay

**Narrator:** "Agent MedIC — SigNoz watches → MCP investigates → LLM diagnoses → Docker fixes → Everything logged. One platform, one agent, total observability."

**Visual:** Team info + GitHub QR + "Star SigNoz on GitHub"

**Narrator:** "Team Enthusiast — Rudra and Het Patel. Thank you!"
