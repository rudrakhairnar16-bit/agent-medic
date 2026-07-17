from config import config
from typing import Optional


class ContextBuilder:
    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL

    def build_context(self, alert: dict, traces: list, metrics: list, logs: list) -> str:
        from llm.prompts import build_diagnosis_prompt
        return build_diagnosis_prompt(alert, traces, metrics, logs)

    def to_ollama_payload(self, context: str) -> dict:
        return {
            "model": self.model,
            "prompt": context,
            "stream": False,
            "temperature": 0,
            "max_tokens": 2048
        }


context_builder = ContextBuilder()
