"""Pydantic schemas for WebSocket messages."""
from pydantic import BaseModel, Field
from typing import Any, List
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """WebSocket message types."""

    # Client -> Server
    AUTH = "AUTH"
    REQUEST_STATE = "REQUEST_STATE"
    ACK_SUCCESS = "ACK_SUCCESS"
    ACK_ERROR = "ACK_ERROR"
    ALARM_TRIGGERED = "ALARM_TRIGGERED"
    ALARM_COMPLETED = "ALARM_COMPLETED"
    HEARTBEAT = "HEARTBEAT"

    # Server -> Client
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAILED = "AUTH_FAILED"
    STATE_SYNC = "STATE_SYNC"
    SET_ALARM = "SET_ALARM"
    DELETE_ALARM = "DELETE_ALARM"
    PONG = "PONG"


class WebSocketMessage(BaseModel):
    """Base WebSocket message schema."""

    type: MessageType
    data: Any = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AuthMessage(BaseModel):
    """Authentication message data."""

    token: str


class AlarmData(BaseModel):
    """Alarm data for WebSocket messages."""

    id: int
    label: str
    time: str
    repeat_days: List[int]
    enabled: bool


class StateSyncData(BaseModel):
    """State sync message data."""

    alarms: List[AlarmData]


class AckMessage(BaseModel):
    """Acknowledgment message data."""

    alarm_id: int
    success: bool
    error: str | None = None


class AlarmEventMessage(BaseModel):
    """Alarm event message data."""

    alarm_id: int
    status: str  # 'started', 'completed', 'stopped_early', 'failed'
    error: str | None = None
