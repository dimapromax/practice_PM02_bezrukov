from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class BookingStatus(Enum):
    """Статусы бронирования"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


class WaitlistStatus(Enum):
    """Статусы ожидания"""
    WAITING = "waiting"
    NOTIFIED = "notified"
    CONVERTED = "converted"
    EXPIRED = "expired"


@dataclass
class Hotel:
    """Отель"""
    id: Optional[int]
    name: str
    address: str
    phone: str
    rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Room:
    """Номер в отеле"""
    id: Optional[int]
    hotel_id: int
    number: str
    capacity: int
    price_per_night: float
    is_active: bool = True
    room_type: str = "standard"  # standard, deluxe, suite


@dataclass
class Booking:
    """Бронирование"""
    id: Optional[int]
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    total_price: float
    status: BookingStatus = BookingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    cancelled_at: Optional[datetime] = None


@dataclass
class WaitlistEntry:
    """
    Запись в очереди ожидания.
    Если номер занят на нужные даты, пользователь может добавиться в очередь.
    При освобождении номера — уведомление.
    """
    id: Optional[int]
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    desired_room_type: Optional[str] = None
    status: WaitlistStatus = WaitlistStatus.WAITING
    created_at: datetime = field(default_factory=datetime.now)
    notified_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None  # когда запись истекает