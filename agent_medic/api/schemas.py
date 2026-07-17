from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class AlertWebhook(BaseModel):
    alert_id: str
    alert_name: str
    severity: str = "info"
    status: str = "firing"
    labels: Optional[dict] = None
    annotations: Optional[dict] = None
    starts_at: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    alert_id: str
    status: str
    severity: str
    created_at: datetime
    resolved_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
