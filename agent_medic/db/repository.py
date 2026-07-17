from db.models import Incident, IncidentStatus
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime


class IncidentRepository:
    def create(self, db: Session, incident: Incident) -> Incident:
        db.add(incident)
        db.flush()
        return incident

    def get_by_id(self, db: Session, incident_id: str) -> Optional[Incident]:
        return db.query(Incident).filter(Incident.id == incident_id).first()

    def get_by_alert_id(self, db: Session, alert_id: str) -> Optional[Incident]:
        return db.query(Incident).filter(Incident.alert_id == alert_id).first()

    def list_all(self, db: Session, page: int = 1, limit: int = 20) -> List[Incident]:
        offset = (page - 1) * limit
        return db.query(Incident).order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()

    def update_status(self, db: Session, incident_id: str, status: IncidentStatus):
        incident = self.get_by_id(db, incident_id)
        if incident:
            incident.status = status.value
            if status == IncidentStatus.RESOLVED:
                incident.resolved_at = datetime.utcnow()
            db.commit()

    def count(self, db: Session) -> int:
        return db.query(Incident).count()

    def count_resolved(self, db: Session) -> int:
        return db.query(Incident).filter(Incident.status == IncidentStatus.RESOLVED.value).count()
