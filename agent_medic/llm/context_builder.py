from config import config

class ContextBuilder:
    def build_context(self, alert, traces, metrics, logs):
        from llm.prompts import build_diagnosis_prompt
        return build_diagnosis_prompt(alert, traces, metrics, logs)
    def to_ollama_payload(self, context):
        return {"model": config.OLLAMA_MODEL, "prompt": context, "stream": False, "temperature": 0, "max_tokens": 2048}

context_builder = ContextBuilder()
