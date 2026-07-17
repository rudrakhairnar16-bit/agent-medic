from config import config
from db.models import SessionLocal, Incident
from api.websocket import manager
import httpx, asyncio, logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _broadcast(msg):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running(): loop.create_task(manager.broadcast(msg))
    except: pass


def _notify_slack(status, iid, error=""):
    if not config.SLACK_WEBHOOK_URL: return
    try:
        httpx.post(config.SLACK_WEBHOOK_URL, json={
            "text": f"{'✅' if status == 'resolved' else '❌'} Agent MedIC — {status}",
            "blocks": [{"type": "section", "text": {"type": "mrkdwn",
                        "value": f"*Incident:* `{iid[:8]}`\n*Status:* {status}\n{error}"}}]
        }, timeout=5)
    except: pass


def _push_signoz(msg):
    if config.DEMO_MODE: return
    try: httpx.post(f"{config.SIGNOZ_API_URL}/api/v1/logs", json={"incident_log": msg}, timeout=5)
    except: pass


def log_resolved(iid, diagnosis, fix_result):
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.id == iid).first()
        if inc:
            inc.status = "resolved"
            inc.resolved_at = datetime.now(timezone.utc)
            db.commit()
            rt = int((inc.resolved_at - inc.created_at).total_seconds()) if inc.created_at else None
        else: rt = None
        msg = {"incident_id": iid, "status": "resolved", "root_cause": diagnosis.get("root_cause",""), "fix_action": fix_result.get("action",""), "resolution_time_seconds": rt}
        _broadcast(msg); _notify_slack("resolved", iid); _push_signoz(msg)
        logger.info(f"Resolved {iid[:8]} in {rt}s")
    except Exception as e: logger.error(f"Log error: {e}")
    finally: db.close()


def log_failed(iid, error):
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.id == iid).first()
        if inc: inc.status = "failed"; db.commit()
        msg = {"incident_id": iid, "status": "failed", "error": error}
        _broadcast(msg); _notify_slack("failed", iid, error); _push_signoz(msg)
        logger.warning(f"Failed {iid[:8]}: {error[:50]}")
    except Exception as e: logger.error(f"Log error: {e}")
    finally: db.close()


incident_logger = type("IL", (), {"log_resolved": log_resolved, "log_failed": log_failed})()
