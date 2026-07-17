import random, time

SCENARIOS = {
    "redis_crash": {
        "traces": [{"trace_id": f"t{i}", "status": "ERROR", "duration_ms": random.randint(2000,8000), "error": "redis: connection refused"} for i in range(3)],
        "metrics": [{"query":"redis_errors_total","value":15},{"query":"cpu_utilization","value":45},{"query":"memory_usage","value":62},{"query":"error_rate","value":23}],
        "logs": [{"ts":time.time(),"severity":"error","body":"Redis pool exhausted at 5000 conns"}],
        "fix": {"root_cause":"Redis pool exhausted","severity":"critical","confidence":0.92,"suggested_fix":"restart_container","fix_params":{"service_name":"redis"}}},
    "cpu_spike": {
        "traces": [{"trace_id": f"t{i}", "status":"OK", "duration_ms": random.randint(800,3000)} for i in range(5)],
        "metrics": [{"query":"cpu_utilization","value":92},{"query":"memory_usage","value":55},{"query":"error_rate","value":2}],
        "logs": [{"ts":time.time(),"severity":"warning","body":"CPU at 92%"}],
        "fix": {"root_cause":"CPU overload 92%","severity":"warning","confidence":0.85,"suggested_fix":"scale_service","fix_params":{"service_name":"sample-app","replicas":3}}},
    "db_timeout": {
        "traces": [{"trace_id": f"t{i}", "status":"ERROR","duration_ms": random.randint(5000,10000), "error":"psycopg2: connection timed out"} for i in range(4)],
        "metrics": [{"query":"cpu_utilization","value":35},{"query":"error_rate","value":18},{"query":"db_connections","value":0}],
        "logs": [{"ts":time.time(),"severity":"error","body":"PostgreSQL timeout after 30s"}],
        "fix": {"root_cause":"PostgreSQL not responding","severity":"critical","confidence":0.88,"suggested_fix":"restart_container","fix_params":{"service_name":"postgres"}}},
    "random_500s": {
        "traces": [{"trace_id": f"t{i}", "status":"ERROR","duration_ms": random.randint(100,500), "error":"HTTP 500"} for i in range(8)],
        "metrics": [{"query":"cpu_utilization","value":40},{"query":"error_rate","value":35}],
        "logs": [{"ts":time.time(),"severity":"error","body":"KeyError in data_processor.py:142"}],
        "fix": {"root_cause":"App error in data_processor — 35% error rate","severity":"warning","confidence":0.65,"suggested_fix":"escalate","fix_params":{}}},
    "network_partition": {
        "traces": [{"trace_id": f"t{i}", "status":"ERROR","duration_ms": random.randint(10000,30000), "error":"socket: name or service not known"} for i in range(6)],
        "metrics": [{"query":"cpu_utilization","value":30},{"query":"error_rate","value":45},{"query":"network_errors","value":28}],
        "logs": [{"ts":time.time(),"severity":"error","body":"Connection refused: downstream unreachable"}],
        "fix": {"root_cause":"Network partition — DNS failing","severity":"critical","confidence":0.82,"suggested_fix":"restart_container","fix_params":{"service_name":"sample-app"}}},
    "disk_full": {
        "traces": [{"trace_id": f"t{i}", "status":"ERROR","duration_ms": random.randint(3000,6000), "error":"OSError: No space left"} for i in range(5)],
        "metrics": [{"query":"disk_usage_percent","value":98},{"query":"error_rate","value":30},{"query":"cpu_utilization","value":50}],
        "logs": [{"ts":time.time(),"severity":"critical","body":"Disk at 98% — logs consuming space"}],
        "fix": {"root_cause":"Disk full at 98%","severity":"critical","confidence":0.9,"suggested_fix":"clear_cache","fix_params":{"cache_type":"redis"}}},
    "memory_leak": {
        "traces": [{"trace_id": f"t{i}", "status":"ERROR","duration_ms": random.randint(500,1500), "error":"MemoryError: 2.1 GiB"} for i in range(7)],
        "metrics": [{"query":"memory_usage","value":96},{"query":"memory_leak_rate","value":45},{"query":"error_rate","value":25}],
        "logs": [{"ts":time.time(),"severity":"critical","body":"Memory 96% — leak in cache layer"}],
        "fix": {"root_cause":"Memory leak — 45MB/min, 96% used","severity":"critical","confidence":0.88,"suggested_fix":"restart_container","fix_params":{"service_name":"sample-app"}}},
    "slow_queries": {
        "traces": [{"trace_id": f"t{i}", "status":"OK","duration_ms": random.randint(5000,15000)} for i in range(10)],
        "metrics": [{"query":"p99_latency_ms","value":12000},{"query":"avg_query_duration_ms","value":4500},{"query":"db_connection_pool_usage","value":85}],
        "logs": [{"ts":time.time(),"severity":"warning","body":"Slow query: SELECT * FROM orders — 8.2s"}],
        "fix": {"root_cause":"Slow DB queries — p99 12s, missing index","severity":"warning","confidence":0.72,"suggested_fix":"scale_service","fix_params":{"service_name":"postgres","replicas":2}}},
    "tls_cert_expiry": {
        "traces": [{"trace_id": f"t{i}", "status":"ERROR","duration_ms": random.randint(200,800), "error":"SSL: CERTIFICATE_VERIFY_FAILED"} for i in range(4)],
        "metrics": [{"query":"tls_handshake_errors","value":22},{"query":"error_rate","value":40}],
        "logs": [{"ts":time.time(),"severity":"error","body":"TLS: cert expired 2 days ago for api.example.com"}],
        "fix": {"root_cause":"TLS cert expired for api.example.com","severity":"critical","confidence":0.91,"suggested_fix":"escalate","fix_params":{}}},
    "oom_kill": {
        "traces": [{"trace_id": f"t{i}", "status":"ERROR","duration_ms": random.randint(100,300), "error":"OOMKilled: exit 137"} for i in range(3)],
        "metrics": [{"query":"memory_usage","value":99},{"query":"oom_kills","value":3},{"query":"cpu_utilization","value":80}],
        "logs": [{"ts":time.time(),"severity":"critical","body":"Container killed by OOM — limit 512MB exceeded"}],
        "fix": {"root_cause":"OOM — container killed, 512MB limit exceeded","severity":"critical","confidence":0.93,"suggested_fix":"restart_container","fix_params":{"service_name":"sample-app"}}},
    "cascading_failure": {
        "traces": [{"trace_id": f"t{i}", "status":"ERROR","duration_ms": random.randint(1000,5000), "error":"HTTP 503: upstream connect error"} for i in range(12)],
        "metrics": [{"query":"error_rate","value":55},{"query":"redis_errors_total","value":10},{"query":"db_connections","value":0},{"query":"cpu_utilization","value":90}],
        "logs": [{"ts":time.time(),"severity":"critical","body":"Cascading: Redis→DB→CPU all degraded"}],
        "fix": {"root_cause":"Cascading failure from Redis to all services","severity":"critical","confidence":0.87,"suggested_fix":"restart_container","fix_params":{"service_name":"redis"}}},
}

class SimulatedDataProvider:
    def get_scenario_names(self): return list(SCENARIOS.keys())
    def get_data(self, name):
        s = SCENARIOS.get(name, SCENARIOS["redis_crash"])
        return {"traces": s["traces"], "metrics": s["metrics"], "logs": s["logs"], "expected_diagnosis": s["fix"]}
    def get_random_alert(self):
        name = random.choice(list(SCENARIOS.keys()))
        return {"alert_id": f"sim_{int(time.time())}", "alert_name": name.replace("_"," ").title(),
                "severity": "critical" if "crash" in name or "timeout" in name else "warning",
                "labels": {"service_name": "sample-app"}, "annotations": {"summary": f"Demo: {name}"},
                "starts_at": time.time(), "scenario": name}

simulated_data = SimulatedDataProvider()
