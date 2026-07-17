from llm.engine import SYSTEM_PROMPT, _build_prompt

def build_diagnosis_prompt(alert, traces, metrics, logs):
    return _build_prompt(alert, traces, metrics, logs)
