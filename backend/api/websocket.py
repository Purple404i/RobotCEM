from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.job_subscriptions: Dict[str, Set[str]] = {}  # job_id -> set of client_ids
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def subscribe_to_job(self, client_id: str, job_id: str):
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        self.job_subscriptions[job_id].add(client_id)
    
    async def send_job_update(self, job_id: str, message: dict):
        """Send update to all clients subscribed to this job"""
        if job_id not in self.job_subscriptions:
            return
        
        subscribers = self.job_subscriptions[job_id]
        disconnected = []
        
        for client_id in subscribers:
            if client_id in self.active_connections:
                for websocket in self.active_connections[client_id]:
                    try:
                        await websocket.send_json(message)
                    except:
                        disconnected.append((websocket, client_id))
        
        # Clean up disconnected clients
        for ws, cid in disconnected:
            self.disconnect(ws, cid)
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        
        for client_id, websockets in self.active_connections.items():
            for websocket in websockets:
                try:
                    await websocket.send_json(message)
                except:
                    disconnected.append((websocket, client_id))
        
        for ws, cid in disconnected:
            self.disconnect(ws, cid)

manager = ConnectionManager()
