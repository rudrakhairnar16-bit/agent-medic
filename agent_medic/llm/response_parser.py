import json


class LLMResponseParser:
    @staticmethod
    def parse(response_text: str) -> dict:
        try:
            data = json.loads(response_text)
            return {
                "root_cause": data.get("root_cause", "Unknown"),
                "severity": data.get("severity", "info"),
                "confidence": float(data.get("confidence", 0.0)),
                "suggested_fix": data.get("suggested_fix", "escalate"),
                "fix_params": data.get("fix_params", {}),
                "evidence": data.get("evidence", []),
                "raw": response_text
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "root_cause": "Failed to parse LLM response",
                "severity": "info",
                "confidence": 0.0,
                "suggested_fix": "escalate",
                "fix_params": {},
                "evidence": [],
                "raw": response_text
            }


response_parser = LLMResponseParser()
