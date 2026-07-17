import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SIGNOZ_MCP_ENABLED: bool = os.getenv("SIGNOZ_MCP_ENABLED", "true").lower() == "true"
    SIGNOZ_MCP_TRANSPORT: str = os.getenv("SIGNOZ_MCP_TRANSPORT", "stdio")
    SIGNOZ_API_URL: str = os.getenv("SIGNOZ_API_URL", "http://localhost:3301")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/agent_medic")

    DOCKER_HOST: str = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")

    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")

    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

    AGENT_WORKERS: int = int(os.getenv("AGENT_WORKERS", "3"))
    AGENT_DEDUP_WINDOW_MINUTES: int = int(os.getenv("AGENT_DEDUP_WINDOW_MINUTES", "5"))
    AGENT_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("AGENT_RATE_LIMIT_PER_MINUTE", "10"))
    AGENT_MAX_RETRIES: int = int(os.getenv("AGENT_MAX_RETRIES", "3"))
    AGENT_ESCALATION_TIMEOUT_MINUTES: int = int(os.getenv("AGENT_ESCALATION_TIMEOUT_MINUTES", "10"))

    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "agent-medic")
    OTEL_ENABLED: bool = os.getenv("OTEL_ENABLED", "true").lower() == "true"

    @property
    def is_demo(self) -> bool:
        return self.DEMO_MODE

    def validate(self):
        errors = []
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        if self.DEMO_MODE:
            return errors
        if self.SIGNOZ_MCP_ENABLED and not self.SIGNOZ_API_URL:
            errors.append("SIGNOZ_API_URL is required when MCP is enabled")
        return errors


config = Config()
