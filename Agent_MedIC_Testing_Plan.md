# AGENT MEDIC — Complete Testing Plan

**Goal:** Zero bugs during demo. Every flow must work 100% on Day 1.

---

## 1. Test Categories (Total: ~50 tests)

| Category | Count | % |
|---|---|---|
| Unit Tests | 20 | 40% |
| Integration Tests | 12 | 25% |
| E2E Tests | 8 | 17% |
| Chaos Tests | 5 | 10% |
| Performance Tests | 3 | 6% |
| UI Tests | 2 | 4% |

---

## 2. Unit Tests (20 tests)

### MCP Client (5 tests)
| # | Test | Priority |
|---|---|---|
| 1 | MCP client connects to SigNoz | P0 |
| 2 | query_traces() returns valid data | P0 |
| 3 | query_metrics() returns valid series | P1 |
| 4 | query_logs() returns valid entries | P1 |
| 5 | MCP down → HTTP fallback triggers | P1 |

### LLM Engine (5 tests)
| # | Test | Priority |
|---|---|---|
| 6 | Ollama server reachable | P0 |
| 7 | LLM output is valid JSON | P0 |
| 8 | Empty telemetry handled gracefully | P1 |
| 9 | Low confidence → escalate/retry | P2 |
| 10 | LLM timeout → fallback model | P1 |

### Fix Executor (5 tests)
| # | Test | Priority |
|---|---|---|
| 11 | Docker container restart works | P0 |
| 12 | Docker Compose scale works | P1 |
| 13 | Invalid container → proper error | P1 |
| 14 | Fix timeout handled | P2 |
| 15 | Post-fix health verify returns status | P0 |

### Incident Pipeline (3 tests)
| # | Test | Priority |
|---|---|---|
| 16 | Incident created in DB on alert | P0 |
| 17 | Duplicate alert → no duplicate incident | P1 |
| 18 | Status transitions: open → resolved | P1 |

### API Endpoints (2 tests)
| # | Test | Priority |
|---|---|---|
| 19 | POST /webhook receives data | P0 |
| 20 | GET /health returns 200 | P2 |

---

## 3. Integration Tests (12 tests)

| # | Test | Priority |
|---|---|---|
| 21 | Alert → Webhook → Incident → DB | P0 |
| 22 | MCP query → LLM receives context | P0 |
| 23 | LLM diagnosis → Fix plan → Executor | P0 |
| 24 | Fix runs → Health check → Logged | P0 |
| 25 | Full lifecycle: Alert → Resolve | P0 |
| 26 | OTel data reaches SigNoz | P0 |
| 27 | Bug trigger → SigNoz alert fires | P0 |
| 28 | Multiple concurrent incidents | P1 |
| 29 | Agent self-metrics in SigNoz | P2 |
| 30 | DB read/write | P1 |
| 31 | MCP + LLM parallel execution | P2 |
| 32 | Unauthorized webhook rejected | P2 |

---

## 4. E2E Tests (8 tests)

| # | Scenario | Expected | Priority |
|---|---|---|---|
| 33 | Redis crash → restart | Redis up, dashboard green | P0 |
| 34 | CPU spike → scale | CPU drops, incident logged | P0 |
| 35 | DB timeout → restart | DB up, app healthy | P0 |
| 36 | Random 500s → detect + log | Error trend flagged | P1 |
| 37 | MCP down → HTTP fallback | Fallback works | P1 |
| 38 | Ollama down → rule-based | Diagnosis via rules | P1 |
| 39 | Docker unavailable → escalate | Escalation logged | P2 |
| 40 | Full demo: all 4 scenarios | All resolved | P0 |

---

## 5. Chaos Tests (5 tests)

| # | Test | Expected | Priority |
|---|---|---|---|
| 41 | Network partition | Retry + circuit breaker | P1 |
| 42 | Memory pressure (256MB) | Graceful OOM handling | P2 |
| 43 | Disk full on DB | Graceful DB failure | P2 |
| 44 | 100 duplicate alerts in 1s | Dedup + rate limit | P1 |
| 45 | Container killed mid-fix | Recovery on restart | P2 |

---

## 6. Performance Tests (3 tests)

| # | Metric | Target | Priority |
|---|---|---|---|
| 46 | Alert → Resolve latency | < 60s (target: 30s) | P0 |
| 47 | 5 concurrent incidents | All processed < 2min | P1 |
| 48 | LLM response time | < 15s per diagnosis | P1 |

---

## 7. UI Tests (2 tests)

| # | Test | Priority |
|---|---|---|
| 49 | WebSocket live updates | P1 |
| 50 | Dashboard numbers match DB | P2 |

---

## 8. Pass Criteria

| Category | Requirement |
|---|---|
| P0 (20 tests) | 100% must pass |
| P1 (18 tests) | At least 14/18 must pass |
| P2 (12 tests) | Nice to have |
| Performance | Alert → Resolve < 60s |
| Demo Script | All 4 scenarios work without manual intervention |

---

## 9. Run Tests

```bash
# P0 only (critical)
pytest -m P0 -v

# All except chaos
pytest -m "not chaos" -v

# Full suite with timings
pytest --durations=5 -v
```

---

*Testing plan for Agents of SigNoz Hackathon 2026*
*Team Enthusiast — Rudra & Het Patel*
