"""WebSocket connection manager for tracking active connections."""
from fastapi import WebSocket
from typing import Dict, List
from utils.logger import logger
import json


class ConnectionManager:
    """Manages WebSocket connections for users."""

    def __init__(self):
        """Initialize connection manager."""
        # Map user_id to list of WebSocket connections
        # (A user might have multiple clients connected)
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Accept and store a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User's ID
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User's ID
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                logger.info(f"WebSocket disconnected for user {user_id}. Remaining connections: {len(self.active_connections[user_id])}")

            # Clean up empty lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_message(self, message: dict, user_id: int):
        """
        Send a message to all connections for a specific user.

        Args:
            message: Message dictionary to send
            user_id: User's ID
        """
        if user_id not in self.active_connections:
            logger.warning(f"No active connections for user {user_id}")
            return

        # Send to all connections for this user
        disconnected = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket, user_id)

    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected users.

        Args:
            message: Message dictionary to send
        """
        for user_id in list(self.active_connections.keys()):
            await self.send_message(message, user_id)

    def is_user_connected(self, user_id: int) -> bool:
        """
        Check if a user has any active connections.

        Args:
            user_id: User's ID

        Returns:
            True if user is connected, False otherwise
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    def get_connection_count(self, user_id: int) -> int:
        """
        Get number of active connections for a user.

        Args:
            user_id: User's ID

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(user_id, []))


# Global connection manager instance
manager = ConnectionManager()
