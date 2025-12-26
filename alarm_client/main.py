"""Main entry point for the alarm client."""
import signal
import sys
import time
from client.scheduler import AlarmScheduler
from client.alarm_runner import AlarmRunner
from client.websocket_client import WebSocketClient
from handlers.message_handler import MessageHandler
from utils.logger import logger
from config import config


class AlarmClient:
    """Main alarm client application."""

    def __init__(self):
        """Initialize the alarm client."""
        self.running = False
        self.scheduler = None
        self.alarm_runner = None
        self.ws_client = None
        self.message_handler = None

    def start(self):
        """Start the alarm client."""
        logger.info("=" * 60)
        logger.info("CV Alarm Client Starting...")
        logger.info("=" * 60)
        logger.info(f"VPS URL: {config.VPS_URL}")
        logger.info(f"Timezone: {config.TIMEZONE}")
        logger.info(f"CV Alarm Root: {config.CV_ALARM_ROOT}")

        # Initialize alarm runner
        self.alarm_runner = AlarmRunner(
            on_triggered=self.on_alarm_triggered,
            on_completed=self.on_alarm_completed
        )

        # Check prerequisites
        success, error = self.alarm_runner.check_prerequisites()
        if not success:
            logger.error(f"Prerequisites check failed: {error}")
            logger.error("Cannot start alarm client without required files")
            sys.exit(1)

        logger.info("Prerequisites check passed")

        # Initialize scheduler
        self.scheduler = AlarmScheduler(alarm_callback=self.on_alarm_fired)
        self.scheduler.start()
        logger.info("Scheduler started")

        # Initialize WebSocket client and message handler
        self.ws_client = WebSocketClient(on_message=self.on_websocket_message)
        self.message_handler = MessageHandler(self.scheduler, self.ws_client)

        # Connect to VPS
        if not self.ws_client.connect():
            logger.error("Failed to connect to VPS")
            sys.exit(1)

        logger.info("WebSocket client started")
        logger.info("=" * 60)
        logger.info("Alarm client running. Press Ctrl+C to stop.")
        logger.info("=" * 60)

        # Set running flag
        self.running = True

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.stop()

    def stop(self):
        """Stop the alarm client."""
        logger.info("=" * 60)
        logger.info("Stopping alarm client...")
        self.running = False

        if self.ws_client:
            self.ws_client.disconnect()
            logger.info("WebSocket client stopped")

        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

        logger.info("Alarm client stopped")
        logger.info("=" * 60)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.running = False

    def on_alarm_fired(self, alarm_id: int):
        """
        Callback when alarm fires (scheduled time reached).

        Args:
            alarm_id: Alarm ID
        """
        logger.info(f"Alarm {alarm_id} fired!")
        self.alarm_runner.run_alarm(alarm_id)

    def on_alarm_triggered(self, alarm_id: int):
        """
        Callback when alarm starts executing.

        Args:
            alarm_id: Alarm ID
        """
        logger.info(f"Alarm {alarm_id} triggered (run_alarm.py started)")

        # Notify server
        if self.ws_client and self.ws_client.connected:
            self.ws_client.send({
                "type": "ALARM_TRIGGERED",
                "data": {
                    "alarm_id": alarm_id,
                    "status": "started"
                }
            })

    def on_alarm_completed(self, alarm_id: int, status: str, error: str | None):
        """
        Callback when alarm execution completes.

        Args:
            alarm_id: Alarm ID
            status: Completion status ('completed', 'failed', 'stopped_early')
            error: Error message if failed
        """
        logger.info(f"Alarm {alarm_id} completed with status: {status}")

        # Notify server
        if self.ws_client and self.ws_client.connected:
            self.ws_client.send({
                "type": "ALARM_COMPLETED",
                "data": {
                    "alarm_id": alarm_id,
                    "status": status,
                    "error": error
                }
            })

    def on_websocket_message(self, message: dict):
        """
        Callback for WebSocket messages.

        Args:
            message: Message dictionary
        """
        if self.message_handler:
            self.message_handler.handle_message(message)


def main():
    """Main entry point."""
    client = AlarmClient()
    client.start()


if __name__ == "__main__":
    main()
