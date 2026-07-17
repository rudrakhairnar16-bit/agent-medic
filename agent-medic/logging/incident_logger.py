from config import config
from db.repository import IncidentRepository
from db.models import SessionLocal
from api.websocket import manager
import httpx
import json


class IncidentLogger:
    def __init__(self):
        self.repo = IncidentRepository()

    def log_resolved(self, incident_id: str, diagnosis: dict, fix_result: dict):
        db = SessionLocal()
        try:
            incident = self.repo.get_by_id(db, incident_id)
            if incident:
                incident.status = "resolved"
                db.commit()

            message = {
                "type": "incident_update",
                "incident_id": incident_id,
                "status": "resolved",
                "root_cause": diagnosis.get("root_cause", "Unknown"),
                "fix": fix_result.get("action", "unknown"),
                "verified": fix_result.get("verified", False)
            }

            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(manager.broadcast(message))
                else:
                    loop.run_until_complete(manager.broadcast(message))
            except Exception:
                pass

            self._push_to_signoz(message)
        except Exception as e:
            print(f"Logging error: {e}")
        finally:
            db.close()

    def log_failed(self, incident_id: str, error: str):
        db = SessionLocal()
        try:
            incident = self.repo.get_by_id(db, incident_id)
            if incident:
                incident.status = "failed"
                db.commit()

            message = {
                "type": "incident_update",
                "incident_id": incident_id,
                "status": "failed",
                "error": error
            }
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(manager.broadcast(message))
            except Exception:
                pass
        finally:
            db.close()

    def _push_to_signoz(self, message: dict):
        try:
            httpx.post(
                f"{config.SIGNOZ_API_URL}/api/v1/logs",
                json=message,
                timeout=5
            )
        except Exception:
            pass


incident_logger = IncidentLogger()
