from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional
from enum import Enum


class WaitlistStatusDTO(str, Enum):
    """DTO статуса ожидания"""
    WAITING = "waiting"
    NOTIFIED = "notified"
    CONVERTED = "converted"
    EXPIRED = "expired"


class WaitlistCreateDTO(BaseModel):
    """DTO для создания записи в очереди ожидания"""
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    desired_room_type: Optional[str] = None

    @field_validator('check_out')
    @classmethod
    def validate_dates(cls, v, info):
        if 'check_in' in info.data and v <= info.data['check_in']:
            raise ValueError('Дата выезда должна быть позже даты заезда')
        return v


class WaitlistResponseDTO(BaseModel):
    """DTO для ответа с записью в очереди"""
    id: int
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    desired_room_type: Optional[str]
    status: str
    created_at: datetime
    notified_at: Optional[datetime]
    converted_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class WaitlistNotificationDTO(BaseModel):
    """DTO для уведомления из очереди ожидания"""
    waitlist_id: int
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    available_room_id: int
    available_room_number: str