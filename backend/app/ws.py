import asyncio
from collections import defaultdict

from fastapi import WebSocket


class Hub:
    """Per-consultation WebSocket fan-out; publish() is safe to call from worker threads."""

    def __init__(self):
        self.conns: dict[str, set[WebSocket]] = defaultdict(set)
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, cid: str, ws: WebSocket):
        await ws.accept()
        self.conns[cid].add(ws)

    def disconnect(self, cid: str, ws: WebSocket):
        self.conns[cid].discard(ws)

    async def _send(self, cid: str, msg: dict):
        for ws in list(self.conns.get(cid, ())):
            try:
                await ws.send_json(msg)
            except Exception:
                self.conns[cid].discard(ws)

    def publish(self, cid: str, msg: dict):
        if self.loop and self.conns.get(cid):
            asyncio.run_coroutine_threadsafe(self._send(cid, msg), self.loop)


hub = Hub()
