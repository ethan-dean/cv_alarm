"""Message handler for processing WebSocket messages."""
from utils.logger import logger


class MessageHandler:
    """Handles incoming WebSocket messages."""

    def __init__(self, scheduler, websocket_client):
        """
        Initialize message handler.

        Args:
            scheduler: AlarmScheduler instance
            websocket_client: WebSocketClient instance
        """
        self.scheduler = scheduler
        self.ws_client = websocket_client

    def handle_message(self, message: dict):
        """
        Process incoming WebSocket message.

        Args:
            message: Message dictionary
        """
        message_type = message.get("type")
        data = message.get("data")

        logger.debug(f"Handling message type: {message_type}")

        if message_type == "AUTH_SUCCESS":
            self.handle_auth_success(data)

        elif message_type == "STATE_SYNC":
            self.handle_state_sync(data)

        elif message_type == "SET_ALARM":
            self.handle_set_alarm(data)

        elif message_type == "DELETE_ALARM":
            self.handle_delete_alarm(data)

        elif message_type == "PONG":
            # Heartbeat response, no action needed
            pass

        else:
            logger.warning(f"Unknown message type: {message_type}")

    def handle_auth_success(self, data):
        """
        Handle successful authentication.

        Args:
            data: Message data
        """
        logger.info("Authentication successful, requesting state sync")

        # Request full state sync
        self.ws_client.send({
            "type": "REQUEST_STATE",
            "timestamp": None
        })

    def handle_state_sync(self, data):
        """
        Handle state synchronization message.

        Args:
            data: Message data with alarms list
        """
        if not data or "alarms" not in data:
            logger.warning("Invalid STATE_SYNC message: missing alarms")
            return

        alarms = data["alarms"]
        logger.info(f"Received state sync with {len(alarms)} alarms")

        # Clear existing alarms
        self.scheduler.clear_all_alarms()

        # Add all alarms from server
        for alarm in alarms:
            try:
                self.scheduler.add_alarm(
                    alarm_id=alarm["id"],
                    time=alarm["time"],
                    repeat_days=alarm["repeat_days"],
                    enabled=alarm["enabled"]
                )

                # Send acknowledgment
                self.ws_client.send({
                    "type": "ACK_SUCCESS",
                    "data": {
                        "alarm_id": alarm["id"],
                        "success": True
                    }
                })

            except Exception as e:
                logger.error(f"Error adding alarm {alarm.get('id')}: {e}")
                self.ws_client.send({
                    "type": "ACK_ERROR",
                    "data": {
                        "alarm_id": alarm.get("id"),
                        "success": False,
                        "error": str(e)
                    }
                })

    def handle_set_alarm(self, data):
        """
        Handle SET_ALARM message (create or update alarm).

        Args:
            data: Alarm data
        """
        if not data:
            logger.warning("Invalid SET_ALARM message: missing data")
            return

        try:
            alarm_id = data["id"]
            logger.info(f"Setting alarm {alarm_id}")

            self.scheduler.add_alarm(
                alarm_id=alarm_id,
                time=data["time"],
                repeat_days=data["repeat_days"],
                enabled=data["enabled"]
            )

            # Send acknowledgment
            self.ws_client.send({
                "type": "ACK_SUCCESS",
                "data": {
                    "alarm_id": alarm_id,
                    "success": True
                }
            })

        except KeyError as e:
            logger.error(f"Missing required field in SET_ALARM: {e}")
            self.ws_client.send({
                "type": "ACK_ERROR",
                "data": {
                    "alarm_id": data.get("id"),
                    "success": False,
                    "error": f"Missing field: {e}"
                }
            })

        except Exception as e:
            logger.error(f"Error setting alarm: {e}")
            self.ws_client.send({
                "type": "ACK_ERROR",
                "data": {
                    "alarm_id": data.get("id"),
                    "success": False,
                    "error": str(e)
                }
            })

    def handle_delete_alarm(self, data):
        """
        Handle DELETE_ALARM message.

        Args:
            data: Alarm data with id
        """
        if not data or "id" not in data:
            logger.warning("Invalid DELETE_ALARM message: missing id")
            return

        try:
            alarm_id = data["id"]
            logger.info(f"Deleting alarm {alarm_id}")

            self.scheduler.remove_alarm(alarm_id)

            # Send acknowledgment
            self.ws_client.send({
                "type": "ACK_SUCCESS",
                "data": {
                    "alarm_id": alarm_id,
                    "success": True
                }
            })

        except Exception as e:
            logger.error(f"Error deleting alarm: {e}")
            self.ws_client.send({
                "type": "ACK_ERROR",
                "data": {
                    "alarm_id": data.get("id"),
                    "success": False,
                    "error": str(e)
                }
            })
