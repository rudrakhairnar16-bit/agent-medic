import os
from dotenv import load_dotenv

load_dotenv()

def _env(key, default=""): return os.getenv(key, default)
def _int(key, default): return int(os.getenv(key, str(default)))
def _bool(key): return os.getenv(key, "false").lower() == "true"

class Config:
    SIGNOZ_MCP_ENABLED = _bool("SIGNOZ_MCP_ENABLED")
    SIGNOZ_MCP_TRANSPORT = _env("SIGNOZ_MCP_TRANSPORT", "stdio")
    SIGNOZ_API_URL = _env("SIGNOZ_API_URL", "http://localhost:3301")
    OLLAMA_BASE_URL = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = _env("OLLAMA_MODEL", "llama3.2")
    OLLAMA_TIMEOUT = _int("OLLAMA_TIMEOUT", 60)
    DATABASE_URL = _env("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/agent_medic")
    DOCKER_HOST = _env("DOCKER_HOST", "unix:///var/run/docker.sock")
    SLACK_WEBHOOK_URL = _env("SLACK_WEBHOOK_URL")
    DEMO_MODE = _bool("DEMO_MODE")
    LOG_LEVEL = _env("LOG_LEVEL", "INFO")
    LOG_FORMAT = _env("LOG_FORMAT", "json")
    AGENT_WORKERS = _int("AGENT_WORKERS", 3)
    AGENT_DEDUP_WINDOW_MINUTES = _int("AGENT_DEDUP_WINDOW_MINUTES", 5)
    AGENT_RATE_LIMIT_PER_MINUTE = _int("AGENT_RATE_LIMIT_PER_MINUTE", 10)
    AGENT_MAX_RETRIES = _int("AGENT_MAX_RETRIES", 3)
    AGENT_ESCALATION_TIMEOUT_MINUTES = _int("AGENT_ESCALATION_TIMEOUT_MINUTES", 10)
    OTEL_EXPORTER_OTLP_ENDPOINT = _env("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    OTEL_SERVICE_NAME = _env("OTEL_SERVICE_NAME", "agent-medic")
    OTEL_ENABLED = _bool("OTEL_ENABLED")

config = Config()
