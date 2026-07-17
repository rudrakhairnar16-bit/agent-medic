from fastapi import APIRouter, Request
from pipeline.queue import incident_queue
from pipeline.dedup import deduplicator
from pipeline.rate_limiter import rate_limiter
from pipeline.correlator import correlator
from db.repository import IncidentRepository
from db.models import Incident, SessionLocal
from incidents.metrics_collector import metrics_collector
import uuid
import logging

alert_router = APIRouter()
incident_repo = IncidentRepository()
logger = logging.getLogger(__name__)


@alert_router.post("/webhook")
async def handle_alert(request: Request):
    body = await request.json()
    alert_id = body.get("alert_id", str(uuid.uuid4()))
    alert_name = body.get("alert_name", "unknown")
    severity = body.get("severity", "info")

    if deduplicator.is_duplicate(alert_id):
        return {"status": "duplicate", "incident_id": None}

    if not rate_limiter.allow():
        return {"status": "rate_limited", "incident_id": None}

    correlator.push(body)
    correlations = correlator.correlate()
    if correlations:
        logger.info(f"Correlated alert {alert_id} — {len(correlations)} groups")
        body["correlations"] = correlations

    incident = Incident(
        alert_id=alert_id,
        alert_name=alert_name,
        severity=severity,
        message=body.get("annotations", {}).get("summary", ""),
        telemetry_data=body
    )
    db = SessionLocal()
    try:
        created = incident_repo.create(db, incident)
        db.commit()

        metrics_collector.increment("incidents_total")

        await incident_queue.enqueue({
            "incident_id": str(created.id),
            "alert_id": alert_id,
            "alert_name": alert_name,
            "severity": severity,
            "body": body
        })
        return {"status": "accepted", "incident_id": str(created.id)}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
