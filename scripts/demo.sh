#!/bin/bash
# Agent MedIC — Automated Demo (works with DEMO_MODE=true)
# Usage: ./scripts/demo.sh [--simulated]

MODE="${1:-}"
BASE="http://localhost:8000"

echo "============================================"
echo "  Agent MedIC — Automated Demo v3"
echo "============================================"
echo ""

if [ "$MODE" == "--simulated" ] || [ "$MODE" == "--demo" ]; then
  echo "Mode: SIMULATED (sending demo alerts via API)"
  echo ""

  SCENARIOS=("redis_crash" "cpu_spike" "db_timeout" "random_500s")

  for i in "${!SCENARIOS[@]}"; do
    s="${SCENARIOS[$i]}"
    echo "[$((i+1))/4] Triggering: $s..."
    curl -s -X POST "$BASE/demo/trigger?scenario=$s" | python -m json.tool 2>/dev/null || echo "  Sent"
    sleep 3
    echo ""
  done

  echo "Waiting 15s for pipeline to process..."
  sleep 15

  echo ""
  echo "=== Incidents in DB ==="
  curl -s "$BASE/incidents?limit=10" | python -m json.tool 2>/dev/null || curl -s "$BASE/incidents"
  echo ""
  echo "=== Stats Summary ==="
  curl -s "$BASE/incidents/stats/summary" | python -m json.tool 2>/dev/null || echo "  (summary endpoint not available)"

else
  echo "Mode: LIVE (requires working docker services at localhost)"
  echo ""

  echo "[1/4] Stopping Redis to trigger crash..."
  docker stop $(docker compose ps -q redis) 2>/dev/null || echo "  (Redis may not be running)"
  sleep 2
  echo "  Sending alert..."
  curl -s -X POST "$BASE/webhook" \
    -H "Content-Type: application/json" \
    -d '{"alert_id":"demo_redis_1","alert_name":"Redis Crash","severity":"critical","labels":{"service_name":"sample-app"},"annotations":{"summary":"Redis connection pool exhausted"}}' \
    | python -m json.tool 2>/dev/null
  sleep 10

  echo ""
  echo "[2/4] Triggering CPU spike..."
  curl -s "http://localhost:8001/trigger/high-cpu" > /dev/null 2>&1 || echo "  (sample-app not reachable)"
  curl -s -X POST "$BASE/webhook" \
    -H "Content-Type: application/json" \
    -d '{"alert_id":"demo_cpu_1","alert_name":"CPU Spike","severity":"warning","labels":{"service_name":"sample-app"},"annotations":{"summary":"CPU > 80%"}}' \
    | python -m json.tool 2>/dev/null
  sleep 10

  echo ""
  echo "[3/4] Triggering DB timeout..."
  curl -s "http://localhost:8001/trigger/db-timeout" > /dev/null 2>&1 || echo "  (sample-app not reachable)"
  curl -s -X POST "$BASE/webhook" \
    -H "Content-Type: application/json" \
    -d '{"alert_id":"demo_db_1","alert_name":"DB Timeout","severity":"critical","labels":{"service_name":"sample-app"},"annotations":{"summary":"PostgreSQL timeout"}}' \
    | python -m json.tool 2>/dev/null
  sleep 10

  echo ""
  echo "[4/4] Triggering random 500s..."
  curl -s "http://localhost:8001/trigger/random-500" > /dev/null 2>&1 || echo "  (sample-app not reachable)"
  curl -s -X POST "$BASE/webhook" \
    -H "Content-Type: application/json" \
    -d '{"alert_id":"demo_500_1","alert_name":"Random 500s","severity":"warning","labels":{"service_name":"sample-app"},"annotations":{"summary":"35% error rate"}}' \
    | python -m json.tool 2>/dev/null
  sleep 5
fi

echo ""
echo "============================================"
echo "  Demo complete!"
echo ""
echo "  Web UI:    http://localhost:3000"
echo "  API:       http://localhost:8000/incidents"
echo "  Health:    http://localhost:8000/health"
echo "  Summary:   http://localhost:8000/incidents/stats/summary"
echo "============================================"
