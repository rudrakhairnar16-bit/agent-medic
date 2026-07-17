import asyncio
import logging
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from api.routes import router
from api.websocket import ws_router
from listeners.alert_listener import alert_router
from db.models import Base
from db.repository import engine
from worker import pipeline_worker
from config import config
import uvicorn


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage()
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


if config.LOG_FORMAT == "json":
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), handlers=[handler])
else:
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent MedIC",
    version="3.1.0",
    description="Self-Healing AI SRE Agent powered by SigNoz MCP",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(alert_router)
app.include_router(router)
app.include_router(ws_router)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
async def startup():
    errors = config.validate()
    if errors:
        for err in errors:
            logger.warning(f"Config issue: {err}")

    if config.OTEL_ENABLED and not config.is_demo:
        try:
            from otel import init_otel
            init_otel()
            logger.info("OpenTelemetry initialized — exporting to SigNoz")
        except Exception as e:
            logger.warning(f"OpenTelemetry init failed (non-fatal): {e}")

    asyncio.create_task(pipeline_worker.start())

    mode = "DEMO" if config.is_demo else "PRODUCTION"
    logger.info(f"Agent MedIC v3.1.0 started — {mode} mode, "
                f"{config.AGENT_WORKERS} workers, "
                f"Ollama: {config.OLLAMA_MODEL}, "
                f"OTel: {config.OTEL_ENABLED and not config.is_demo}")


@app.on_event("shutdown")
async def shutdown():
    pipeline_worker.stop()
    logger.info("Agent MedIC stopped")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
