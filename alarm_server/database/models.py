"""SQLAlchemy ORM models for the alarm system."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.database import Base


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    alarms = relationship("Alarm", back_populates="user", cascade="all, delete-orphan")
    connection_status = relationship("ConnectionStatus", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Alarm(Base):
    """Alarm model storing alarm configurations."""

    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String(50), default="Alarm")
    time = Column(String(5), nullable=False)  # Format: "HH:MM"
    repeat_days = Column(Text, nullable=False, default="[]")  # JSON array: [0,1,2,3,4,5,6]
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alarms")
    history = relationship("AlarmHistory", back_populates="alarm", cascade="all, delete-orphan")


class ConnectionStatus(Base):
    """Connection status model tracking client connectivity."""

    __tablename__ = "connection_status"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    last_connected = Column(DateTime, nullable=True)
    last_disconnected = Column(DateTime, nullable=True)
    is_online = Column(Boolean, default=False)
    client_version = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="connection_status")


class AlarmHistory(Base):
    """Alarm history model logging alarm events."""

    __tablename__ = "alarm_history"

    id = Column(Integer, primary_key=True, index=True)
    alarm_id = Column(Integer, ForeignKey("alarms.id"), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), nullable=False)  # 'started', 'completed', 'stopped_early', 'failed'
    error_message = Column(Text, nullable=True)

    # Relationships
    alarm = relationship("Alarm", back_populates="history")
