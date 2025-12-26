"""Business logic for alarm operations."""
from sqlalchemy.orm import Session
from database.models import Alarm, AlarmHistory
from schemas.alarm import AlarmCreate, AlarmUpdate
from typing import List
import json


def get_alarms(db: Session, user_id: int) -> List[Alarm]:
    """
    Get all alarms for a user.

    Args:
        db: Database session
        user_id: User's ID

    Returns:
        List of alarm objects
    """
    return db.query(Alarm).filter(Alarm.user_id == user_id).order_by(Alarm.created_at).all()


def get_alarm(db: Session, alarm_id: int, user_id: int) -> Alarm | None:
    """
    Get a specific alarm by ID.

    Args:
        db: Database session
        alarm_id: Alarm's ID
        user_id: User's ID (for authorization)

    Returns:
        Alarm object if found and belongs to user, None otherwise
    """
    return db.query(Alarm).filter(Alarm.id == alarm_id, Alarm.user_id == user_id).first()


def create_alarm(db: Session, alarm_data: AlarmCreate, user_id: int) -> Alarm:
    """
    Create a new alarm.

    Args:
        db: Database session
        alarm_data: Alarm creation data
        user_id: User's ID

    Returns:
        Created alarm object
    """
    alarm = Alarm(
        user_id=user_id,
        label=alarm_data.label,
        time=alarm_data.time,
        repeat_days=json.dumps(alarm_data.repeat_days),
        enabled=alarm_data.enabled
    )
    db.add(alarm)
    db.commit()
    db.refresh(alarm)
    return alarm


def update_alarm(db: Session, alarm_id: int, alarm_data: AlarmUpdate, user_id: int) -> Alarm | None:
    """
    Update an existing alarm.

    Args:
        db: Database session
        alarm_id: Alarm's ID
        alarm_data: Alarm update data
        user_id: User's ID (for authorization)

    Returns:
        Updated alarm object if found, None otherwise
    """
    alarm = get_alarm(db, alarm_id, user_id)
    if not alarm:
        return None

    # Update only provided fields
    if alarm_data.label is not None:
        alarm.label = alarm_data.label
    if alarm_data.time is not None:
        alarm.time = alarm_data.time
    if alarm_data.repeat_days is not None:
        alarm.repeat_days = json.dumps(alarm_data.repeat_days)
    if alarm_data.enabled is not None:
        alarm.enabled = alarm_data.enabled

    db.commit()
    db.refresh(alarm)
    return alarm


def toggle_alarm(db: Session, alarm_id: int, enabled: bool, user_id: int) -> Alarm | None:
    """
    Toggle alarm enabled status.

    Args:
        db: Database session
        alarm_id: Alarm's ID
        enabled: New enabled status
        user_id: User's ID (for authorization)

    Returns:
        Updated alarm object if found, None otherwise
    """
    alarm = get_alarm(db, alarm_id, user_id)
    if not alarm:
        return None

    alarm.enabled = enabled
    db.commit()
    db.refresh(alarm)
    return alarm


def delete_alarm(db: Session, alarm_id: int, user_id: int) -> bool:
    """
    Delete an alarm.

    Args:
        db: Database session
        alarm_id: Alarm's ID
        user_id: User's ID (for authorization)

    Returns:
        True if alarm was deleted, False if not found
    """
    alarm = get_alarm(db, alarm_id, user_id)
    if not alarm:
        return False

    db.delete(alarm)
    db.commit()
    return True


def log_alarm_event(db: Session, alarm_id: int, status: str, error_message: str | None = None) -> AlarmHistory:
    """
    Log an alarm event to history.

    Args:
        db: Database session
        alarm_id: Alarm's ID
        status: Event status ('started', 'completed', 'stopped_early', 'failed')
        error_message: Optional error message

    Returns:
        Created alarm history entry
    """
    history = AlarmHistory(
        alarm_id=alarm_id,
        status=status,
        error_message=error_message
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
