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

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    AGENT_WORKERS: int = int(os.getenv("AGENT_WORKERS", "3"))
    AGENT_DEDUP_WINDOW_MINUTES: int = int(os.getenv("AGENT_DEDUP_WINDOW_MINUTES", "5"))
    AGENT_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("AGENT_RATE_LIMIT_PER_MINUTE", "10"))


config = Config()
