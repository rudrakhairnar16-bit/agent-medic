#!/bin/bash
echo "============================================"
echo "  Agent MedIC — Automated Demo Sequence"
echo "============================================"
echo ""

echo "[1/4] Triggering Redis crash..."
docker stop $(docker compose ps -q redis) 2>/dev/null
echo "  Waiting 15s for detection + fix..."
sleep 15
echo "  Done."
echo ""

echo "[2/4] Triggering CPU spike..."
curl -s http://localhost:8001/trigger/high-cpu > /dev/null
sleep 5
echo "  Waiting 15s for detection + fix..."
sleep 15
curl -s -X POST http://localhost:8001/trigger/high-cpu/stop > /dev/null
echo "  Done."
echo ""

echo "[3/4] Triggering DB timeout..."
curl -s http://localhost:8001/trigger/db-timeout > /dev/null
sleep 5
echo "  Waiting 15s for detection + fix..."
sleep 15
echo "  Done."
echo ""

echo "[4/4] Triggering random 500 errors..."
curl -s http://localhost:8001/trigger/random-500 > /dev/null
sleep 5
curl -s http://localhost:8001/trigger/random-500 > /dev/null
echo "  Done."
echo ""

echo "============================================"
echo "  Demo complete! Check dashboard:"
echo "  http://localhost:3000"
echo "============================================"
