"""
CloudPulse WebSocket Manager
Maintains active real-time dashboard connections and broadcasts telemetry updates.
"""
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger("CloudPulse.WebSocket")


class ConnectionManager:
    def __init__(self):
        # org_id -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: str):
        await websocket.accept()
        if org_id not in self.active_connections:
            self.active_connections[org_id] = []
        self.active_connections[org_id].append(websocket)
        logger.info(f"WebSocket client connected to org {org_id}. Total: {len(self.active_connections[org_id])}")

    def disconnect(self, websocket: WebSocket, org_id: str):
        if org_id in self.active_connections and websocket in self.active_connections[org_id]:
            self.active_connections[org_id].remove(websocket)
            logger.info(f"WebSocket client disconnected from org {org_id}. Remaining: {len(self.active_connections[org_id])}")

    async def broadcast_to_org(self, org_id: str, message: Dict[str, Any]):
        """Broadcasts a JSON message to all connected clients of a specific organization."""
        if org_id not in self.active_connections:
            return

        dead_sockets = []
        for connection in self.active_connections[org_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send to client: {e}")
                dead_sockets.append(connection)

        for dead in dead_sockets:
            self.disconnect(dead, org_id)

    async def broadcast_all(self, message: Dict[str, Any]):
        """Broadcasts to all connected organizations."""
        for org_id in list(self.active_connections.keys()):
            await self.broadcast_to_org(org_id, message)


ws_manager = ConnectionManager()
