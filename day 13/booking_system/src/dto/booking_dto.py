from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional
from enum import Enum


class BookingStatusDTO(str, Enum):
    """DTO статуса бронирования"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


class BookingCreateDTO(BaseModel):
    """DTO для создания бронирования"""
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date

    @field_validator('check_out')
    @classmethod
    def validate_dates(cls, v, info):
        if 'check_in' in info.data and v <= info.data['check_in']:
            raise ValueError('Дата выезда должна быть позже даты заезда')
        if 'check_in' in info.data and (v - info.data['check_in']).days > 30:
            raise ValueError('Бронирование не может превышать 30 дней')
        return v


class BookingResponseDTO(BaseModel):
    """DTO для ответа с бронированием"""
    id: int
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    total_price: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class BookingUpdateDTO(BaseModel):
    """DTO для обновления бронирования"""
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None


class BookingSearchDTO(BaseModel):
    """DTO для поиска бронирований"""
    room_id: Optional[int] = None
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    status: Optional[BookingStatusDTO] = None
    check_in_from: Optional[date] = None
    check_in_to: Optional[date] = None