from pydantic import BaseModel
from typing import Optional

class AlertWebhook(BaseModel):
    alert_id: str
    alert_name: str
    severity: str = "info"
    status: str = "firing"
    labels: Optional[dict] = None
    annotations: Optional[dict] = None
    starts_at: Optional[str] = None
