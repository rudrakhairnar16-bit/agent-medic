from config import config
from db.repository import IncidentRepository
from db.models import SessionLocal
from api.websocket import manager
import httpx
import json
import logging

logger = logging.getLogger(__name__)


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

            resolution_time = None
            if incident and incident.created_at:
                from datetime import datetime, timezone
                resolution_time = int(
                    (datetime.now(timezone.utc) - incident.created_at).total_seconds()
                )

            message = {
                "type": "incident_update",
                "incident_id": incident_id,
                "status": "resolved",
                "root_cause": diagnosis.get("root_cause", "Unknown"),
                "fix_action": fix_result.get("action", "unknown"),
                "verified": fix_result.get("verified", False),
                "resolution_time_seconds": resolution_time,
                "simulated": fix_result.get("simulated", False)
            }

            self._broadcast(message)
            self._push_to_signoz(message)
            self._notify_slack(message)

            logger.info(f"Incident {incident_id} resolved in {resolution_time}s — "
                        f"{diagnosis.get('root_cause', '')}")
        except Exception as e:
            logger.error(f"Logging error for {incident_id}: {e}")
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
            self._broadcast(message)
            self._notify_slack(message)
            logger.warning(f"Incident {incident_id} failed: {error}")
        except Exception as e:
            logger.error(f"Failed to log failure for {incident_id}: {e}")
        finally:
            db.close()

    def log_escalation(self, incident_id: str, diagnosis: dict):
        db = SessionLocal()
        try:
            incident = self.repo.get_by_id(db, incident_id)
            if incident:
                incident.status = "escalated"
                db.commit()

            message = {
                "type": "incident_update",
                "incident_id": incident_id,
                "status": "escalated",
                "root_cause": diagnosis.get("root_cause", "Unknown"),
                "error": "Escalated to human — confidence too low or max retries exceeded"
            }
            self._broadcast(message)
            self._notify_slack(message)
            logger.info(f"Incident {incident_id} escalated to human")
        finally:
            db.close()

    def _broadcast(self, message: dict):
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(manager.broadcast(message))
        except Exception:
            pass

    def _push_to_signoz(self, message: dict):
        if config.is_demo:
            return
        try:
            httpx.post(
                f"{config.SIGNOZ_API_URL}/api/v1/logs",
                json={"incident_log": message},
                timeout=5
            )
        except Exception:
            pass

    def _notify_slack(self, message: dict):
        if not config.SLACK_WEBHOOK_URL:
            return
        try:
            status_icon = "✅" if message.get("status") == "resolved" else "❌"
            slack_msg = {
                "text": f"{status_icon} Agent MedIC — Incident {message.get('status', 'update')}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "value": (
                                f"*Incident:* `{message.get('incident_id', 'N/A')[:8]}`\n"
                                f"*Status:* {message.get('status', 'unknown')}\n"
                                f"*Root Cause:* {message.get('root_cause', 'N/A')}\n"
                                f"*Error:* {message.get('error', 'N/A')}\n"
                                f"*Resolution Time:* {message.get('resolution_time_seconds', 'N/A')}s"
                            )
                        }
                    }
                ]
            }
            httpx.post(config.SLACK_WEBHOOK_URL, json=slack_msg, timeout=5)
        except Exception:
            pass


incident_logger = IncidentLogger()
