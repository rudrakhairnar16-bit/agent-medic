from fastapi import FastAPI, HTTPException
from instrument import instrument_app
import random, time, os, threading

app = FastAPI(title="Sample App")
instrument_app(app)

CPU_BUG_ENABLED = False
MEMORY_BUG_ENABLED = False
DB_BUG_ENABLED = False
ERROR_RATE_BUG_ENABLED = False

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/app")


@app.get("/")
def root():
    return {"service": "sample-app", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/trigger/high-cpu")
def trigger_high_cpu():
    global CPU_BUG_ENABLED
    CPU_BUG_ENABLED = True
    threading.Thread(target=_cpu_intensive_task, daemon=True).start()
    return {"status": "triggered", "bug": "high-cpu"}


def _cpu_intensive_task():
    while CPU_BUG_ENABLED:
        _ = [i ** 2 for i in range(10000)]
        time.sleep(0.1)


@app.post("/trigger/high-cpu/stop")
def stop_high_cpu():
    global CPU_BUG_ENABLED
    CPU_BUG_ENABLED = False
    return {"status": "stopped", "bug": "high-cpu"}


@app.get("/trigger/memory-leak")
def trigger_memory_leak():
    global MEMORY_BUG_ENABLED
    MEMORY_BUG_ENABLED = True
    threading.Thread(target=_memory_leak_task, daemon=True).start()
    return {"status": "triggered", "bug": "memory-leak"}


leaked_data = []
def _memory_leak_task():
    while MEMORY_BUG_ENABLED:
        leaked_data.append(" " * 1024 * 1024)
        time.sleep(1)


@app.post("/trigger/memory-leak/stop")
def stop_memory_leak():
    global MEMORY_BUG_ENABLED
    MEMORY_BUG_ENABLED = False
    leaked_data.clear()
    return {"status": "stopped", "bug": "memory-leak"}


@app.get("/trigger/db-timeout")
def trigger_db_timeout():
    global DB_BUG_ENABLED
    DB_BUG_ENABLED = True
    return {"status": "triggered", "bug": "db-timeout"}


@app.get("/trigger/random-500")
def trigger_random_500():
    global ERROR_RATE_BUG_ENABLED
    ERROR_RATE_BUG_ENABLED = not ERROR_RATE_BUG_ENABLED
    return {"status": "triggered" if ERROR_RATE_BUG_ENABLED else "stopped", "bug": "random-500"}


@app.get("/api/data")
def get_data():
    if DB_BUG_ENABLED:
        time.sleep(random.uniform(3, 8))
        raise HTTPException(status_code=503, detail="Database timeout")

    if ERROR_RATE_BUG_ENABLED and random.random() < 0.3:
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"data": "ok", "timestamp": time.time()}


@app.get("/api/redis-test")
def redis_test():
    import redis
    try:
        r = redis.Redis.from_url(redis_url, socket_timeout=2)
        r.ping()
        return {"redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {str(e)}")
