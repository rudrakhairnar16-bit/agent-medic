import asyncio
import logging
from fastapi import FastAPI
from api.routes import router
from api.websocket import ws_router
from listeners.alert_listener import alert_router
from db.models import Base
from db.repository import engine
from worker import pipeline_worker
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent MedIC", version="2.0.0")

app.include_router(alert_router)
app.include_router(router)
app.include_router(ws_router)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
async def startup():
    asyncio.create_task(pipeline_worker.start())
    logger.info("Agent MedIC started — pipeline worker running")


@app.on_event("shutdown")
async def shutdown():
    pipeline_worker.stop()
    logger.info("Agent MedIC stopped")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
