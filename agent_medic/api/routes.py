from fastapi import APIRouter, Depends
from db.models import SessionLocal, Incident
from sqlalchemy.orm import Session

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health():
    return {"status": "healthy"}


@router.get("/incidents")
def list_incidents(page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    offset = (page - 1) * limit
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()
    total = db.query(Incident).count()
    return {"incidents": [i.to_dict() for i in incidents], "total": total, "page": page}


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return {"error": "not found"}
    return {"incident": incident.to_dict()}


@router.get("/metrics")
def agent_metrics(db: Session = Depends(get_db)):
    total = db.query(Incident).count()
    resolved = db.query(Incident).filter(Incident.status == "resolved").count()
    return {"total": total, "resolved": resolved, "failed": total - resolved}
