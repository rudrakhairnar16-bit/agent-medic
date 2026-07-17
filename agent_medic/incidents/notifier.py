import httpx
from config import config
notifier = type("N", (), {"send": staticmethod(lambda msg: httpx.post(config.SLACK_WEBHOOK_URL, json={"text": msg}, timeout=5)) if config.SLACK_WEBHOOK_URL else lambda msg: None})()
