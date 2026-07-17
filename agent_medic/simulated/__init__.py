from simulated.data import simulated_data

class SimulatedMCPClient:
    def query_traces(self, svc="app", tr="now-5m"): return {"result": simulated_data.get_data("redis_crash")["traces"], "simulated": True}
    def query_metrics(self, q="", tr="now-5m"): return {"result": simulated_data.get_data("redis_crash")["metrics"], "simulated": True}
    def query_logs(self, svc="app", tr="now-5m"): return {"result": simulated_data.get_data("redis_crash")["logs"], "simulated": True}
    def get_alerts(self): return {"result": [{"alert_id":"sim_001","name":"Demo"}]}
    def connect(self): pass

class SimulatedFixExecutor:
    async def execute(self, action, params):
        import asyncio; await asyncio.sleep(2)
        return {"status":"success","action":action,"message":f"Simulated: {action}","verified":True,"simulated":True}

class SimulatedOllamaClient:
    def diagnose(self, alert, traces, metrics, logs):
        d = dict(simulated_data.get_data(alert.get("scenario","redis_crash"))["expected_diagnosis"])
        d["simulated"] = True; return d

def get_simulated_deps():
    return {"mcp": SimulatedMCPClient(), "fix": SimulatedFixExecutor(), "llm": SimulatedOllamaClient()}
