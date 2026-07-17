import httpx
from config import config


class Notifier:
    def __init__(self):
        self.slack_webhook = None

    def set_slack_webhook(self, url: str):
        self.slack_webhook = url

    def send(self, message: str):
        if self.slack_webhook:
            try:
                httpx.post(self.slack_webhook, json={"text": message}, timeout=5)
            except Exception:
                pass


notifier = Notifier()
