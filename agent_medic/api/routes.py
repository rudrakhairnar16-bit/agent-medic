import time, asyncio
from fastapi import APIRouter, Depends
from db.models import SessionLocal, Incident
from config import config
from incidents.metrics_collector import metrics_collector

router = APIRouter()
_start = time.time()

def _db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/health")
def health():
    from worker import pipeline_worker
    from pipeline.queue import incident_queue
    worker_alive = pipeline_worker.running
    queue_depth = incident_queue.qsize()
    return {
        "status": "healthy" if worker_alive else "degraded",
        "version": "3.1.0",
        "mode": "demo" if config.DEMO_MODE else "production",
        "uptime": int(time.time() - _start),
        "worker_alive": worker_alive,
        "queue_depth": queue_depth,
        "workers_configured": config.AGENT_WORKERS,
        "model": config.OLLAMA_MODEL,
    }

@router.get("/incidents")
def list_incidents(page=1, limit=20, db=Depends(_db)):
    off = (page - 1) * limit
    items = db.query(Incident).order_by(Incident.created_at.desc()).offset(off).limit(limit).all()
    total = db.query(Incident).count()
    return {"incidents": [i.to_dict() for i in items], "total": total, "page": page, "pages": max(1, (total + limit - 1) // limit)}

@router.get("/incidents/{iid}")
def get_incident(iid: str, db=Depends(_db)):
    inc = db.query(Incident).filter(Incident.id == iid).first()
    return {"error": "not found", "incident_id": iid} if not inc else {"incident": inc.to_dict()}

@router.get("/incidents/stats/summary")
def summary(db=Depends(_db)):
    total = db.query(Incident).count()
    resolved = db.query(Incident).filter(Incident.status == "resolved").count()
    failed = db.query(Incident).filter(Incident.status == "failed").count()
    open_ = db.query(Incident).filter(Incident.status.in_(["open","investigating","diagnosing","fixing"])).count()
    return {"total": total, "resolved": resolved, "failed": failed, "open": open_, "rate": round(resolved / max(total, 1) * 100, 1)}

@router.get("/metrics")
def agent_metrics(): return metrics_collector.snapshot()

@router.post("/demo/trigger")
async def trigger(scenario="redis_crash"):
    if not config.DEMO_MODE: return {"error": "DEMO_MODE not enabled"}
    from pipeline.queue import rate_limiter, incident_queue
    if not rate_limiter.allow(): return {"status": "rate_limited", "error": "Too many requests"}
    from simulated.data import simulated_data
    names = simulated_data.get_scenario_names()
    if scenario not in names: return {"error": f"Invalid. Choose: {names}"}
    db = SessionLocal()
    try:
        inc = Incident(alert_id=f"demo_{scenario}_{int(time.time())}", alert_name=scenario.replace("_"," ").title(), severity="critical", message=f"Demo: {scenario}",
                       telemetry_data={"scenario": scenario})
        db.add(inc); db.commit()
        await incident_queue.enqueue({"incident_id": str(inc.id), "body": {"scenario": scenario, "alert_id": inc.alert_id}})
        return {"status": "triggered", "scenario": scenario, "incident_id": str(inc.id)}
    except Exception as e: db.rollback(); return {"error": str(e)}
    finally: db.close()
