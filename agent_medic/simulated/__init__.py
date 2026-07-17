from simulated.data import simulated_data
from mcp.client import MCPResponseParser, QUERY_TEMPLATES
import sys

def _get_global_metrics():
    """Resolve the global metrics_collector avoiding double-import issues."""
    mod = sys.modules.get("incidents.metrics_collector") or sys.modules.get("agent_medic.incidents.metrics_collector")
    if mod:
        return mod.metrics_collector
    from incidents.metrics_collector import metrics_collector
    return metrics_collector

parser = MCPResponseParser()

class SimulatedMetricsCollector:
    @property
    def _real(self): return _get_global_metrics()
    def increment(self, k): self._real.increment(k)
    def snapshot(self): return self._real.snapshot()
    def reset(self): self._real.reset()

class SimulatedIncidentLogger:
    def log_resolved(self, iid, diagnosis, fix_result): pass
    def log_failed(self, iid, error): pass

class SimulatedMCPClient:
    def __init__(self, scenario="redis_crash"):
        self.scenario = scenario

    def set_scenario(self, name):
        if name in simulated_data.get_scenario_names():
            self.scenario = name

    def query_traces(self, svc="app", tr="now-5m"):
        return {"result": simulated_data.get_data(self.scenario)["traces"], "simulated": True}
    def query_metrics(self, q="", tr="now-5m"):
        return {"result": simulated_data.get_data(self.scenario)["metrics"], "simulated": True}
    def query_logs(self, svc="app", tr="now-5m"):
        return {"result": simulated_data.get_data(self.scenario)["logs"], "simulated": True}
    def get_alerts(self): return {"result": [{"alert_id":"sim_001","name":"Demo"}]}
    def connect(self): pass

class SimulatedFixExecutor:
    async def execute(self, action, params):
        import asyncio; await asyncio.sleep(2)
        return {"status":"success","action":action,"message":f"Simulated: {action}","verified":True,"simulated":True}

class SimulatedOllamaClient:
    def diagnose(self, alert, traces, metrics, logs, correlation=None):
        d = dict(simulated_data.get_data(alert.get("scenario","redis_crash"))["expected_diagnosis"])
        d["simulated"] = True; return d

def get_simulated_deps(scenario="redis_crash"):
    return {"mcp": SimulatedMCPClient(scenario=scenario), "fix": SimulatedFixExecutor(), "llm": SimulatedOllamaClient(),
            "mcp_parser": parser, "mcp_queries": QUERY_TEMPLATES,
            "metrics": SimulatedMetricsCollector(), "logger": SimulatedIncidentLogger()}
