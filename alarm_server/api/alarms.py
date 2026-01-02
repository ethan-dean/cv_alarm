"""REST API endpoints for alarm CRUD operations."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from database.database import get_db
from database.models import User
from schemas.alarm import AlarmCreate, AlarmUpdate, AlarmResponse, AlarmToggle
from services import alarm_service
from services.connection_manager import manager
from api.auth import get_current_user
from utils.logger import logger

router = APIRouter(prefix="/api/alarms", tags=["alarms"])


@router.get("", response_model=List[AlarmResponse])
def list_alarms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all alarms for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of alarms
    """
    alarms = alarm_service.get_alarms(db, current_user.id)
    return [AlarmResponse.from_orm(alarm) for alarm in alarms]


@router.get("/{alarm_id}", response_model=AlarmResponse)
def get_alarm(
    alarm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific alarm by ID.

    Args:
        alarm_id: Alarm ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Alarm object

    Raises:
        HTTPException: If alarm not found
    """
    alarm = alarm_service.get_alarm(db, alarm_id, current_user.id)
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm with id {alarm_id} not found"
        )
    return AlarmResponse.from_orm(alarm)


@router.post("", response_model=AlarmResponse, status_code=status.HTTP_201_CREATED)
async def create_alarm(
    alarm_data: AlarmCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new alarm.

    Args:
        alarm_data: Alarm creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created alarm object
    """
    alarm = alarm_service.create_alarm(db, alarm_data, current_user.id)
    logger.info(f"User {current_user.username} created alarm {alarm.id}: {alarm.time}")

    # Send WebSocket message to connected clients
    alarm_response = AlarmResponse.from_orm(alarm)
    await manager.send_message({
        "type": "SET_ALARM",
        "data": alarm_response.model_dump(mode='json'),
        "timestamp": datetime.utcnow().isoformat()
    }, current_user.id)

    return alarm_response


@router.put("/{alarm_id}", response_model=AlarmResponse)
async def update_alarm(
    alarm_id: int,
    alarm_data: AlarmUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing alarm.

    Args:
        alarm_id: Alarm ID
        alarm_data: Alarm update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated alarm object

    Raises:
        HTTPException: If alarm not found
    """
    alarm = alarm_service.update_alarm(db, alarm_id, alarm_data, current_user.id)
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm with id {alarm_id} not found"
        )

    logger.info(f"User {current_user.username} updated alarm {alarm.id}")

    # Send WebSocket message to connected clients
    alarm_response = AlarmResponse.from_orm(alarm)
    await manager.send_message({
        "type": "SET_ALARM",
        "data": alarm_response.model_dump(mode='json'),
        "timestamp": datetime.utcnow().isoformat()
    }, current_user.id)

    return alarm_response


@router.patch("/{alarm_id}/toggle", response_model=AlarmResponse)
async def toggle_alarm(
    alarm_id: int,
    toggle_data: AlarmToggle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle alarm enabled status.

    Args:
        alarm_id: Alarm ID
        toggle_data: Toggle data with enabled status
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated alarm object

    Raises:
        HTTPException: If alarm not found
    """
    alarm = alarm_service.toggle_alarm(db, alarm_id, toggle_data.enabled, current_user.id)
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm with id {alarm_id} not found"
        )

    logger.info(f"User {current_user.username} {'enabled' if toggle_data.enabled else 'disabled'} alarm {alarm.id}")

    # Send WebSocket message to connected clients
    alarm_response = AlarmResponse.from_orm(alarm)
    await manager.send_message({
        "type": "SET_ALARM",
        "data": alarm_response.model_dump(mode='json'),
        "timestamp": datetime.utcnow().isoformat()
    }, current_user.id)

    return alarm_response


@router.delete("/{alarm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alarm(
    alarm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an alarm.

    Args:
        alarm_id: Alarm ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If alarm not found
    """
    success = alarm_service.delete_alarm(db, alarm_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm with id {alarm_id} not found"
        )

    logger.info(f"User {current_user.username} deleted alarm {alarm_id}")

    # Send WebSocket message to connected clients
    await manager.send_message({
        "type": "DELETE_ALARM",
        "data": {"id": alarm_id},
        "timestamp": datetime.utcnow().isoformat()
    }, current_user.id)

    return None
