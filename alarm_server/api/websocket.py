"""WebSocket endpoint for real-time alarm synchronization."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User, ConnectionStatus
from services.connection_manager import manager
from services import alarm_service
from schemas.websocket import MessageType, WebSocketMessage, AlarmData
from schemas.alarm import AlarmResponse
from utils.security import decode_access_token
from utils.logger import logger
from datetime import datetime
import json

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time communication with alarm clients.

    Args:
        websocket: WebSocket connection
        token: JWT authentication token (query parameter)
        db: Database session
    """
    # Authenticate user via token
    token_data = decode_access_token(token)
    if not token_data:
        await websocket.close(code=1008, reason="Invalid authentication token")
        logger.warning("WebSocket connection rejected: Invalid token")
        return

    # Get user from database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        await websocket.close(code=1008, reason="User not found")
        logger.warning(f"WebSocket connection rejected: User {token_data.user_id} not found")
        return

    # Accept connection
    await manager.connect(websocket, user.id)

    # Update connection status
    connection_status = db.query(ConnectionStatus).filter(ConnectionStatus.user_id == user.id).first()
    if not connection_status:
        connection_status = ConnectionStatus(user_id=user.id)
        db.add(connection_status)

    connection_status.is_online = True
    connection_status.last_connected = datetime.utcnow()
    db.commit()

    logger.info(f"User {user.username} connected via WebSocket")

    # Send authentication success
    await websocket.send_json({
        "type": MessageType.AUTH_SUCCESS,
        "data": None,
        "timestamp": datetime.utcnow().isoformat()
    })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")

            logger.debug(f"Received WebSocket message from user {user.username}: {message_type}")

            # Handle different message types
            if message_type == MessageType.REQUEST_STATE:
                await handle_request_state(websocket, user.id, db)

            elif message_type == MessageType.ACK_SUCCESS:
                await handle_ack_success(data.get("data"), user.id, db)

            elif message_type == MessageType.ACK_ERROR:
                await handle_ack_error(data.get("data"), user.id, db)

            elif message_type == MessageType.ALARM_TRIGGERED:
                await handle_alarm_triggered(data.get("data"), user.id, db)

            elif message_type == MessageType.ALARM_COMPLETED:
                await handle_alarm_completed(data.get("data"), user.id, db)

            elif message_type == MessageType.HEARTBEAT:
                # Respond with PONG
                await websocket.send_json({
                    "type": MessageType.PONG,
                    "data": None,
                    "timestamp": datetime.utcnow().isoformat()
                })

            else:
                logger.warning(f"Unknown message type received: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"User {user.username} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.username}: {e}")
    finally:
        # Clean up connection
        manager.disconnect(websocket, user.id)

        # Update connection status
        connection_status = db.query(ConnectionStatus).filter(ConnectionStatus.user_id == user.id).first()
        if connection_status:
            connection_status.is_online = manager.is_user_connected(user.id)
            connection_status.last_disconnected = datetime.utcnow()
            db.commit()


async def handle_request_state(websocket: WebSocket, user_id: int, db: Session):
    """
    Handle REQUEST_STATE message by sending all alarms to client.

    Args:
        websocket: WebSocket connection
        user_id: User's ID
        db: Database session
    """
    alarms = alarm_service.get_alarms(db, user_id)

    alarm_data_list = []
    for alarm in alarms:
        alarm_response = AlarmResponse.from_orm(alarm)
        alarm_data_list.append({
            "id": alarm_response.id,
            "label": alarm_response.label,
            "time": alarm_response.time,
            "repeat_days": alarm_response.repeat_days,
            "enabled": alarm_response.enabled
        })

    await websocket.send_json({
        "type": MessageType.STATE_SYNC,
        "data": {"alarms": alarm_data_list},
        "timestamp": datetime.utcnow().isoformat()
    })

    logger.info(f"Sent state sync with {len(alarm_data_list)} alarms to user {user_id}")


async def handle_ack_success(data: dict, user_id: int, db: Session):
    """
    Handle ACK_SUCCESS message from client.

    Args:
        data: Message data
        user_id: User's ID
        db: Database session
    """
    alarm_id = data.get("alarm_id")
    logger.info(f"User {user_id} acknowledged successful scheduling of alarm {alarm_id}")


async def handle_ack_error(data: dict, user_id: int, db: Session):
    """
    Handle ACK_ERROR message from client.

    Args:
        data: Message data
        user_id: User's ID
        db: Database session
    """
    alarm_id = data.get("alarm_id")
    error = data.get("error", "Unknown error")
    logger.error(f"User {user_id} reported error scheduling alarm {alarm_id}: {error}")


async def handle_alarm_triggered(data: dict, user_id: int, db: Session):
    """
    Handle ALARM_TRIGGERED message from client.

    Args:
        data: Message data
        user_id: User's ID
        db: Database session
    """
    alarm_id = data.get("alarm_id")
    logger.info(f"Alarm {alarm_id} triggered for user {user_id}")

    # Log to alarm history
    alarm_service.log_alarm_event(db, alarm_id, "started")


async def handle_alarm_completed(data: dict, user_id: int, db: Session):
    """
    Handle ALARM_COMPLETED message from client.

    Args:
        data: Message data
        user_id: User's ID
        db: Database session
    """
    alarm_id = data.get("alarm_id")
    status = data.get("status", "completed")
    error = data.get("error")

    logger.info(f"Alarm {alarm_id} completed for user {user_id} with status: {status}")

    # Log to alarm history
    alarm_service.log_alarm_event(db, alarm_id, status, error)


async def send_alarm_update(user_id: int, alarm, action: str):
    """
    Send alarm update to connected clients.

    Args:
        user_id: User's ID
        alarm: Alarm object
        action: Action type ('SET_ALARM' or 'DELETE_ALARM')
    """
    if action == "DELETE_ALARM":
        message = {
            "type": MessageType.DELETE_ALARM,
            "data": {"id": alarm.id},
            "timestamp": datetime.utcnow().isoformat()
        }
    else:  # SET_ALARM
        alarm_response = AlarmResponse.from_orm(alarm)
        message = {
            "type": MessageType.SET_ALARM,
            "data": {
                "id": alarm_response.id,
                "label": alarm_response.label,
                "time": alarm_response.time,
                "repeat_days": alarm_response.repeat_days,
                "enabled": alarm_response.enabled
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    await manager.send_message(message, user_id)
