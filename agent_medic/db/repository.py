from db.models import Incident
from sqlalchemy.orm import Session

class IncidentRepository:
    def __init__(self): pass
    def create(self, db, incident): db.add(incident); db.flush(); return incident
    def get_by_id(self, db, iid): return db.query(Incident).filter(Incident.id == iid).first()
    def list_all(self, db, page=1, limit=20): return db.query(Incident).order_by(Incident.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    def count(self, db): return db.query(Incident).count()
