from config import config
from simulated.data import simulated_data
from typing import Optional


class SimulatedMCPClient:
    def query_traces(self, service: str = "sample-app", time_range: str = "now-5m") -> dict:
        return {"result": simulated_data.get_data("redis_crash")["traces"], "simulated": True}

    def query_metrics(self, query: str = "", time_range: str = "now-5m") -> dict:
        return {"result": simulated_data.get_data("redis_crash")["metrics"], "simulated": True}

    def query_logs(self, service: str = "sample-app", time_range: str = "now-5m") -> dict:
        return {"result": simulated_data.get_data("redis_crash")["logs"], "simulated": True}

    def get_alerts(self) -> dict:
        return {"result": [{"alert_id": "sim_001", "name": "Demo Alert"}]}

    def connect(self):
        pass


class SimulatedFixExecutor:
    async def execute(self, action_type: str, params: dict) -> dict:
        import asyncio
        await asyncio.sleep(2)
        return {
            "status": "success",
            "action": action_type,
            "message": f"Simulated: {action_type} with {params}",
            "verified": True,
            "simulated": True
        }


class SimulatedOllamaClient:
    def diagnose(self, alert: dict, traces: list, metrics: list, logs: list) -> dict:
        scenario_name = alert.get("scenario", "")
        data = simulated_data.get_data(scenario_name)
        diagnosis = dict(data["expected_diagnosis"])
        diagnosis["simulated"] = True
        return diagnosis


def get_simulated_deps():
    return {
        "mcp": SimulatedMCPClient(),
        "fix": SimulatedFixExecutor(),
        "llm": SimulatedOllamaClient()
    }
