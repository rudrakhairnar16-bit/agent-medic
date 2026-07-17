from fastapi import FastAPI
from api.routes import router
from api.websocket import ws_router
from listeners.alert_listener import alert_router
from db.models import Base
from db.repository import engine
import uvicorn

app = FastAPI(title="Agent MedIC", version="2.0.0")

app.include_router(alert_router)
app.include_router(router)
app.include_router(ws_router)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
async def startup():
    pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
