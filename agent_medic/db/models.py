from sqlalchemy import create_engine, Column, String, Text, Integer, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from config import config
import uuid
from datetime import datetime, timezone

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(255))
    alert_name = Column(String(255))
    status = Column(String(50), default="open")
    severity = Column(String(20))
    source_service = Column(String(255), default="unknown")
    message = Column(Text)
    telemetry_data = Column(JSON)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if isinstance(getattr(self, c.name), datetime) else getattr(self, c.name))
                for c in self.__table__.columns}
