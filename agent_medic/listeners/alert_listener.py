from fastapi import APIRouter, Request
from api.schemas import AlertWebhook
from pipeline.queue import incident_queue, deduplicator, rate_limiter, correlator
from db.models import Incident, SessionLocal
from incidents.metrics_collector import metrics_collector
from config import config

alert_router = APIRouter()

@alert_router.post("/webhook")
async def handle_alert(body: AlertWebhook, request: Request):
    if config.WEBHOOK_SECRET:
        key = request.headers.get("X-Api-Key", "")
        if key != config.WEBHOOK_SECRET:
            return {"status": "unauthorized"}
    raw = body.model_dump() if hasattr(body, "model_dump") else body
    aid = raw.get("alert_id")
    if deduplicator.is_duplicate(aid): return {"status": "duplicate"}
    if not rate_limiter.allow(): return {"status": "rate_limited"}
    correlator.push(raw)
    if config.DEMO_MODE:
        import uuid
        iid = str(uuid.uuid4())
        metrics_collector.increment("incidents_total")
        await incident_queue.enqueue({"incident_id": iid, "alert_id": aid, "body": raw})
        return {"status": "accepted", "incident_id": iid, "mode": "demo"}
    db = SessionLocal()
    try:
        inc = Incident(alert_id=aid, alert_name=raw.get("alert_name","unknown"), severity=raw.get("severity","info"),
                       message=(raw.get("annotations") or {}).get("summary",""), telemetry_data=raw)
        db.add(inc); db.commit()
        metrics_collector.increment("incidents_total")
        await incident_queue.enqueue({"incident_id": str(inc.id), "alert_id": aid, "body": raw})
        return {"status": "accepted", "incident_id": str(inc.id)}
    except Exception as e: db.rollback(); return {"status": "error", "message": str(e)}
    finally: db.close()
