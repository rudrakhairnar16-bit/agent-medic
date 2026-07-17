import asyncio, logging, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from api.routes import router
from api.websocket import ws_router
from listeners.alert_listener import alert_router
from db.models import Base, engine
from worker import pipeline_worker
from config import config

fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), format=fmt)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent MedIC", version="3.1.0", description="Self-Healing AI SRE Agent")
app.include_router(alert_router)
app.include_router(router)
app.include_router(ws_router)
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup():
    if config.OTEL_ENABLED and not config.DEMO_MODE:
        try:
            from otel import init_otel
            init_otel(); logger.info("OTel initialized")
        except Exception as e: logger.warning(f"OTel skipped: {e}")
    asyncio.create_task(pipeline_worker.start())
    logger.info(f"v3.1.0 {'DEMO' if config.DEMO_MODE else 'PRODUCTION'} — {config.AGENT_WORKERS} workers, {config.OLLAMA_MODEL}")

@app.on_event("shutdown")
async def shutdown():
    await pipeline_worker.stop()
    logger.info("Stopped")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
