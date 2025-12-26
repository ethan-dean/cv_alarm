"""WebSocket client for alarm synchronization with the VPS."""
import websocket
import json
import threading
import time
import requests
from typing import Callable
from config import config
from utils.logger import logger


class WebSocketClient:
    """WebSocket client with automatic reconnection."""

    def __init__(self, on_message: Callable):
        """
        Initialize WebSocket client.

        Args:
            on_message: Callback function to handle incoming messages
        """
        self.on_message = on_message
        self.ws = None
        self.token = None
        self.running = False
        self.connected = False
        self.reconnect_delay = config.RECONNECT_INITIAL_DELAY
        self.reconnect_thread = None
        self.heartbeat_thread = None

    def authenticate(self) -> bool:
        """
        Authenticate with the REST API to get JWT token.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            response = requests.post(
                f"{config.REST_API_URL}/login",
                json={
                    "username": config.USERNAME,
                    "password": config.PASSWORD
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def connect(self):
        """Start the WebSocket connection."""
        self.running = True

        # Authenticate first
        if not self.authenticate():
            logger.error("Failed to authenticate, cannot connect")
            return False

        # Start connection in background thread
        self.reconnect_thread = threading.Thread(target=self._connect_loop)
        self.reconnect_thread.daemon = True
        self.reconnect_thread.start()

        return True

    def disconnect(self):
        """Stop the WebSocket connection."""
        self.running = False
        self.connected = False

        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None

        logger.info("WebSocket client disconnected")

    def send(self, message: dict):
        """
        Send a message to the server.

        Args:
            message: Message dictionary to send
        """
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message: {e}")
        else:
            logger.warning("Cannot send message: not connected")

    def _connect_loop(self):
        """Main connection loop with reconnection logic."""
        while self.running:
            try:
                # Build WebSocket URL with token and client_type
                ws_url = f"{config.VPS_URL}?token={self.token}&client_type=alarm_client"

                logger.info(f"Connecting to WebSocket: {ws_url.split('?')[0]}...")

                # Create WebSocket connection
                self.ws = websocket.WebSocketApp(
                    ws_url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    on_open=self._on_open
                )

                # Run WebSocket (blocking)
                self.ws.run_forever()

            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")

            # If we're still running, attempt reconnection
            if self.running:
                logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                time.sleep(self.reconnect_delay)

                # Exponential backoff
                self.reconnect_delay = min(
                    self.reconnect_delay * config.RECONNECT_MULTIPLIER,
                    config.RECONNECT_MAX_DELAY
                )

                # Re-authenticate before reconnecting
                self.authenticate()

    def _on_open(self, ws):
        """Handle WebSocket connection opened."""
        logger.info("WebSocket connected")
        self.connected = True
        self.reconnect_delay = config.RECONNECT_INITIAL_DELAY

        # Start heartbeat
        self._start_heartbeat()

    def _on_message(self, ws, message):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            self.on_message(data)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _on_error(self, ws, error):
        """Handle WebSocket error."""
        logger.error(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closed."""
        logger.info(f"WebSocket closed (code: {close_status_code}, msg: {close_msg})")
        self.connected = False
        self._stop_heartbeat()

    def _start_heartbeat(self):
        """Start sending periodic heartbeat messages."""
        def heartbeat_loop():
            while self.connected and self.running:
                try:
                    self.send({
                        "type": "HEARTBEAT",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    })
                    time.sleep(30)  # Send heartbeat every 30 seconds
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    break

        self.heartbeat_thread = threading.Thread(target=heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def _stop_heartbeat(self):
        """Stop heartbeat thread."""
        # Thread will stop automatically when self.connected becomes False
        pass
