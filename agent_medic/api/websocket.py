from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self): self.active = set()
    async def connect(self, ws): await ws.accept(); self.active.add(ws)
    def disconnect(self, ws): self.active.discard(ws)
    async def broadcast(self, msg):
        dead = set()
        for ws in self.active:
            try: await ws.send_json(msg)
            except: dead.add(ws)
        self.active -= dead

manager = ConnectionManager()
