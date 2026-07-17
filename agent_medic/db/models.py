from sqlalchemy import create_engine, Column, String, Text, Integer, Float, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import declarative_base, sessionmaker
from config import config
import enum
import uuid
from datetime import datetime

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    DIAGNOSING = "diagnosing"
    FIXING = "fixing"
    RESOLVED = "resolved"
    FAILED = "failed"
    ESCALATED = "escalated"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(255))
    alert_name = Column(String(255))
    status = Column(String(50), default=IncidentStatus.OPEN.value)
    severity = Column(String(20))
    source_service = Column(String(255), default="unknown")
    message = Column(Text)
    telemetry_data = Column(JSON)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "alert_name": self.alert_name,
            "status": self.status,
            "severity": self.severity,
            "source_service": self.source_service,
            "message": self.message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }
