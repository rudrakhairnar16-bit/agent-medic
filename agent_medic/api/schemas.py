from pydantic import BaseModel, Field
from typing import Optional

class AlertWebhook(BaseModel):
    alert_id: str = Field(..., description="SigNoz alert ID")
    alert_name: str = Field(..., description="Alert rule name")
    severity: str = "warning"
    status: str = "firing"
    labels: Optional[dict] = None
    annotations: Optional[dict] = None
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    generator_url: Optional[str] = None
    fingerprint: Optional[str] = None
    silenced: Optional[bool] = False
    resolved: Optional[bool] = False
    value: Optional[float] = None
    threshold: Optional[float] = None
    rule_id: Optional[int] = None
