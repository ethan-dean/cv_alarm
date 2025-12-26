"""Pydantic schemas for alarm-related operations."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List
import re
import json


class AlarmBase(BaseModel):
    """Base schema for alarm with common fields."""

    label: str = Field(default="Alarm", max_length=50)
    time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    repeat_days: List[int] = Field(default_factory=list)
    enabled: bool = True

    @field_validator("repeat_days")
    @classmethod
    def validate_repeat_days(cls, v):
        """Validate repeat_days contains only valid day indices (0-6)."""
        if not isinstance(v, list):
            raise ValueError("repeat_days must be a list")
        for day in v:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise ValueError("repeat_days must contain integers between 0 and 6")
        # Remove duplicates and sort
        return sorted(list(set(v)))


class AlarmCreate(AlarmBase):
    """Schema for creating a new alarm."""
    pass


class AlarmUpdate(BaseModel):
    """Schema for updating an existing alarm (all fields optional)."""

    label: str | None = Field(default=None, max_length=50)
    time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    repeat_days: List[int] | None = None
    enabled: bool | None = None

    @field_validator("repeat_days")
    @classmethod
    def validate_repeat_days(cls, v):
        """Validate repeat_days if provided."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("repeat_days must be a list")
        for day in v:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise ValueError("repeat_days must contain integers between 0 and 6")
        return sorted(list(set(v)))


class AlarmResponse(AlarmBase):
    """Schema for alarm response."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Convert ORM object to Pydantic model, parsing repeat_days JSON."""
        data = {
            "id": obj.id,
            "user_id": obj.user_id,
            "label": obj.label,
            "time": obj.time,
            "repeat_days": json.loads(obj.repeat_days) if isinstance(obj.repeat_days, str) else obj.repeat_days,
            "enabled": obj.enabled,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at
        }
        return cls(**data)


class AlarmToggle(BaseModel):
    """Schema for toggling alarm enabled status."""

    enabled: bool
