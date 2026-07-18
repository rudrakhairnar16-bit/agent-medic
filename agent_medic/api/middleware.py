import collections, time

webhook_calls = collections.defaultdict(list)
WEBHOOK_RATE = 20
WEBHOOK_WINDOW = 60

def check_webhook_rate(ip):
    now = time.time()
    webhook_calls[ip] = [t for t in webhook_calls[ip] if now - t < WEBHOOK_WINDOW]
    if len(webhook_calls[ip]) >= WEBHOOK_RATE:
        return False
    webhook_calls[ip].append(now)
    return True
