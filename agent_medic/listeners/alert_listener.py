from fastapi import APIRouter, Request
from pipeline.queue import incident_queue, deduplicator, rate_limiter, correlator
from db.models import Incident, SessionLocal
from incidents.metrics_collector import metrics_collector

alert_router = APIRouter()

@alert_router.post("/webhook")
async def handle_alert(req: Request):
    body = await req.json()
    aid = body.get("alert_id")
    if deduplicator.is_duplicate(aid): return {"status": "duplicate"}
    if not rate_limiter.allow(): return {"status": "rate_limited"}
    correlator.push(body)
    db = SessionLocal()
    try:
        inc = Incident(alert_id=aid, alert_name=body.get("alert_name","unknown"), severity=body.get("severity","info"),
                       message=body.get("annotations",{}).get("summary",""), telemetry_data=body)
        db.add(inc); db.commit()
        metrics_collector.increment("incidents_total")
        await incident_queue.enqueue({"incident_id": str(inc.id), "alert_id": aid, "body": body})
        return {"status": "accepted", "incident_id": str(inc.id)}
    except Exception as e: db.rollback(); return {"status": "error", "message": str(e)}
    finally: db.close()
