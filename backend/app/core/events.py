import asyncio
import json
from typing import Dict, List, Set, Any
from fastapi import WebSocket


class EventBroadcaster:
    """Manages real-time event distribution for active analysis sessions via WebSockets and SSE."""

    def __init__(self):
        # WebSocket active connections by analysis_id
        self._ws_connections: Dict[str, Set[WebSocket]] = {}
        # SSE asyncio queues by analysis_id
        self._sse_queues: Dict[str, List[asyncio.Queue]] = {}

    async def connect_ws(self, analysis_id: str, websocket: WebSocket):
        await websocket.accept()
        if analysis_id not in self._ws_connections:
            self._ws_connections[analysis_id] = set()
        self._ws_connections[analysis_id].add(websocket)

    def disconnect_ws(self, analysis_id: str, websocket: WebSocket):
        if analysis_id in self._ws_connections:
            self._ws_connections[analysis_id].discard(websocket)
            if not self._ws_connections[analysis_id]:
                del self._ws_connections[analysis_id]

    def subscribe_sse(self, analysis_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if analysis_id not in self._sse_queues:
            self._sse_queues[analysis_id] = []
        self._sse_queues[analysis_id].append(q)
        return q

    def unsubscribe_sse(self, analysis_id: str, q: asyncio.Queue):
        if analysis_id in self._sse_queues:
            if q in self._sse_queues[analysis_id]:
                self._sse_queues[analysis_id].remove(q)
            if not self._sse_queues[analysis_id]:
                del self._sse_queues[analysis_id]

    async def broadcast(self, analysis_id: str, event_type: str, data: Dict[str, Any]):
        """Publish event to all WebSocket and SSE listeners for analysis_id."""
        payload = {
            "analysis_id": analysis_id,
            "event": event_type,
            "data": data,
        }
        json_str = json.dumps(payload)

        # 1. Broadcast to WebSockets
        if analysis_id in self._ws_connections:
            dead_sockets = set()
            for ws in list(self._ws_connections[analysis_id]):
                try:
                    await ws.send_text(json_str)
                except Exception:
                    dead_sockets.add(ws)
            for ws in dead_sockets:
                self.disconnect_ws(analysis_id, ws)

        # 2. Broadcast to SSE Queues
        if analysis_id in self._sse_queues:
            for q in list(self._sse_queues[analysis_id]):
                try:
                    await q.put(payload)
                except Exception:
                    pass


event_broadcaster = EventBroadcaster()

