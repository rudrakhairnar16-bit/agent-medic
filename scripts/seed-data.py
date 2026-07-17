#!/usr/bin/env python3
"""Seed script — triggers all 4 bug scenarios and sends simulated alerts to Agent MedIC."""
import httpx
import time
import json
import sys

AGENT_URL = "http://localhost:8000"
SAMPLE_APP_URL = "http://localhost:8001"
SIMULATED = "--simulated" in sys.argv or "--demo" in sys.argv


def trigger_bug(name: str, url: str):
    print(f"  Triggering: {name}...")
    try:
        resp = httpx.get(url, timeout=10)
        print(f"    Response: {resp.status_code} — {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"    Failed: {e}")
        return False


def send_webhook(alert_data: dict):
    print(f"  Sending alert: {alert_data['alert_name']}...")
    try:
        resp = httpx.post(f"{AGENT_URL}/webhook", json=alert_data, timeout=10)
        print(f"    Response: {resp.status_code} — {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"    Failed: {e}")
        return False


def check_incidents():
    try:
        resp = httpx.get(f"{AGENT_URL}/incidents?limit=5", timeout=10)
        data = resp.json()
        print(f"    Incidents in DB: {data.get('total', 0)}")
        return data.get("incidents", [])
    except Exception as e:
        print(f"    Failed to fetch incidents: {e}")
        return []


print("=" * 60)
print("  Agent MedIC — Seed Data Loader")
print("=" * 60)
print()

if SIMULATED:
    print("Mode: SIMULATED (no real services needed)")
    print()

    scenarios = [
        {
            "alert_id": "seed_redis_001",
            "alert_name": "Redis Crash",
            "severity": "critical",
            "labels": {"service_name": "sample-app"},
            "annotations": {"summary": "Redis connection pool exhausted"},
            "starts_at": time.time(),
            "scenario": "redis_crash"
        },
        {
            "alert_id": "seed_cpu_001",
            "alert_name": "CPU Spike",
            "severity": "warning",
            "labels": {"service_name": "sample-app"},
            "annotations": {"summary": "CPU utilization exceeds 80%"},
            "starts_at": time.time(),
            "scenario": "cpu_spike"
        },
        {
            "alert_id": "seed_db_001",
            "alert_name": "DB Timeout",
            "severity": "critical",
            "labels": {"service_name": "sample-app"},
            "annotations": {"summary": "PostgreSQL connection timeout"},
            "starts_at": time.time(),
            "scenario": "db_timeout"
        },
        {
            "alert_id": "seed_500_001",
            "alert_name": "Random 500 Errors",
            "severity": "warning",
            "labels": {"service_name": "sample-app"},
            "annotations": {"summary": "35% error rate detected"},
            "starts_at": time.time(),
            "scenario": "random_500s"
        }
    ]

    for scenario in scenarios:
        send_webhook(scenario)
        time.sleep(1)

    print()
    print("Waiting 10s for pipeline to process...")
    time.sleep(10)

    print()
    incidents = check_incidents()
    for inc in incidents:
        print(f"  - {inc['id'][:8]}: {inc['status']} — {inc.get('message', 'N/A')[:50]}")
else:
    print("Mode: LIVE (requires running services)")
    print()

    print("[1/4] Triggering bugs on sample-app...")
    trigger_bug("Redis app crash", f"{SAMPLE_APP_URL}/trigger/db-timeout")
    time.sleep(2)

    print()
    print("[2/4] Sending alerts via webhook...")
    alerts = [
        {
            "alert_id": f"live_alert_{int(time.time())}",
            "alert_name": "High Error Rate",
            "severity": "critical",
            "labels": {"service_name": "sample-app"},
            "annotations": {"summary": "Error rate > 5% for 5 minutes"}
        },
        {
            "alert_id": f"live_cpu_{int(time.time())}",
            "alert_name": "High CPU Usage",
            "severity": "warning",
            "labels": {"service_name": "sample-app"},
            "annotations": {"summary": "CPU utilization > 80%"}
        }
    ]
    for alert in alerts:
        send_webhook(alert)
        time.sleep(1)

    print()
    print("[3/4] Starting load test...")
    trigger_bug("CPU spike", f"{SAMPLE_APP_URL}/trigger/high-cpu")

    print()
    print("[4/4] Checking results...")
    time.sleep(5)
    incidents = check_incidents()

print()
print("=" * 60)
print("  Seed complete!")
print(f"  Dashboard: http://localhost:3000")
print(f"  API:       http://localhost:8000/incidents")
print("=" * 60)
