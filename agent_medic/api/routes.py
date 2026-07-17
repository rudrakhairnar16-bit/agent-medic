from fastapi import APIRouter, Depends
from db.models import SessionLocal, Incident
from db.repository import IncidentRepository
from incidents.metrics_collector import metrics_collector
from config import config
from sqlalchemy.orm import Session
import time

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "mode": "demo" if config.is_demo else "production",
        "uptime_seconds": int(time.time() - _start_time),
        "workers": config.AGENT_WORKERS,
        "ollama_model": config.OLLAMA_MODEL
    }


_start_time = time.time()


@router.get("/incidents")
def list_incidents(page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    offset = (page - 1) * limit
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()
    total = db.query(Incident).count()
    return {
        "incidents": [i.to_dict() for i in incidents],
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit)
    }


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return {"error": "not found", "incident_id": incident_id}
    return {"incident": incident.to_dict()}


@router.get("/incidents/stats/summary")
def incident_summary(db: Session = Depends(get_db)):
    total = db.query(Incident).count()
    resolved = db.query(Incident).filter(Incident.status == "resolved").count()
    failed = db.query(Incident).filter(Incident.status == "failed").count()
    open_incidents = db.query(Incident).filter(
        Incident.status.in_(["open", "investigating", "diagnosing", "fixing"])
    ).count()
    return {
        "total": total,
        "resolved": resolved,
        "failed": failed,
        "open": open_incidents,
        "resolution_rate": round(resolved / max(total, 1) * 100, 1)
    }


@router.get("/metrics")
def agent_metrics():
    return metrics_collector.snapshot()


@router.post("/demo/trigger")
def trigger_demo_scenario(scenario: str = "redis_crash"):
    if not config.is_demo:
        return {"error": "Demo mode not enabled. Set DEMO_MODE=true"}
    from simulated.data import simulated_data
    from pipeline.queue import incident_queue
    import asyncio

    names = simulated_data.get_scenario_names()
    if scenario not in names:
        return {"error": f"Unknown scenario. Choose from: {names}"}

    alert = {
        "alert_id": f"demo_{scenario}_{int(time.time())}",
        "alert_name": scenario.replace("_", " ").title(),
        "severity": "critical",
        "labels": {"service_name": "sample-app"},
        "annotations": {"summary": f"Demo: {scenario}"},
        "starts_at": time.time(),
        "scenario": scenario
    }

    from db.models import Incident as IncidentModel
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        incident = IncidentModel(
            alert_id=alert["alert_id"],
            alert_name=alert["alert_name"],
            severity=alert["severity"],
            message=f"Demo: {scenario}",
            telemetry_data=alert
        )
        db.add(incident)
        db.commit()

        asyncio.create_task(asyncio.to_thread(
            lambda: asyncio.run(incident_queue.enqueue({
                "incident_id": str(incident.id),
                "alert_id": alert["alert_id"],
                "body": alert
            }))
        ))
        return {"status": "triggered", "scenario": scenario, "incident_id": str(incident.id)}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
