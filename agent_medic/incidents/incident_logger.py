from config import config
from db.models import SessionLocal, Incident
from api.websocket import manager
import httpx, asyncio, logging, json, sys
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _degraded_incident_update(iid, status, **kw):
    logger.error("DB unavailable: incident %s status=%s (degraded mode)", iid[:8], status)
    sys.stderr.write(f"[DEGRADED] incident={iid[:8]} status={status} data={json.dumps(kw)}\n")


def _broadcast(msg):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running(): loop.create_task(manager.broadcast(msg))
    except Exception as e:
        logger.warning("Broadcast failed: %s", e)


def _notify_slack(status, iid, error=""):
    if not config.SLACK_WEBHOOK_URL: return
    try:
        httpx.post(config.SLACK_WEBHOOK_URL, json={
            "text": f"Agent MedIC — {status}",
            "blocks": [{"type": "section", "text": {"type": "mrkdwn",
                        "value": f"*Incident:* `{iid[:8]}`\n*Status:* {status}\n{error}"}}]
        }, timeout=5)
    except Exception as e:
        logger.warning("Slack notify failed: %s", e)


def _push_signoz(msg):
    if config.DEMO_MODE: return
    try:
        httpx.post(f"{config.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/logs",
                   json={"resourceLogs": [{"scopeLogs": [{"logRecords": [{"body": {"stringValue": json.dumps(msg)}, "severityText": "INFO"}]}]}]},
                   timeout=5)
    except Exception as e:
        logger.warning("SigNoz log push failed: %s", e)


def log_resolved(iid, diagnosis, fix_result):
    try:
        db = SessionLocal()
    except Exception as e:
        logger.error("DB connection failed (resolved): %s", e)
        _degraded_incident_update(iid, "resolved", root_cause=diagnosis.get("root_cause",""), fix_action=fix_result.get("action",""))
        msg = {"incident_id": iid, "status": "resolved", "root_cause": diagnosis.get("root_cause",""), "fix_action": fix_result.get("action","")}
        _broadcast(msg); _notify_slack("resolved", iid); _push_signoz(msg)
        return
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
        logger.info("Resolved %s in %ss", iid[:8], rt)
    except Exception as e: logger.error("Log error: %s", e)
    finally: db.close()


def log_failed(iid, error):
    try:
        db = SessionLocal()
    except Exception as e:
        logger.error("DB connection failed (failed): %s", e)
        _degraded_incident_update(iid, "failed", error=error[:50])
        msg = {"incident_id": iid, "status": "failed", "error": error}
        _broadcast(msg); _notify_slack("failed", iid, error); _push_signoz(msg)
        return
    try:
        inc = db.query(Incident).filter(Incident.id == iid).first()
        if inc: inc.status = "failed"; db.commit()
        msg = {"incident_id": iid, "status": "failed", "error": error}
        _broadcast(msg); _notify_slack("failed", iid, error); _push_signoz(msg)
        logger.warning("Failed %s: %s", iid[:8], error[:50])
    except Exception as e: logger.error("Log error: %s", e)
    finally: db.close()


class IncidentLogger:
    log_resolved = staticmethod(log_resolved)
    log_failed = staticmethod(log_failed)

incident_logger = IncidentLogger()
