from contextlib import contextmanager
from typing import Type

from src.repositories.booking_repo import BookingRepository
from src.repositories.hotel_repo import HotelRepository
from src.repositories.room_repo import RoomRepository
from src.repositories.waitlist_repo import WaitlistRepository


class UnitOfWork:
    """
    Unit of Work - управляет транзакциями.
    В реальном проекте здесь был бы session.commit() / session.rollback().
    """

    def __init__(self):
        self._hotel_repo = HotelRepository()
        self._room_repo = RoomRepository()
        self._booking_repo = BookingRepository()
        self._waitlist_repo = WaitlistRepository()
        self._committed = False
        self._rolled_back = False

    @property
    def hotels(self) -> HotelRepository:
        return self._hotel_repo

    @property
    def rooms(self) -> RoomRepository:
        return self._room_repo

    @property
    def bookings(self) -> BookingRepository:
        return self._booking_repo

    @property
    def waitlist(self) -> WaitlistRepository:
        return self._waitlist_repo

    def commit(self) -> None:
        """
        Фиксация транзакции.
        В реальном проекте: session.commit()
        """
        self._committed = True

    def rollback(self) -> None:
        """
        Откат транзакции.
        В реальном проекте: session.rollback()
        """
        self._rolled_back = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        elif not self._committed and not self._rolled_back:
            self.commit()

    def reset(self):
        """Сброс состояния (для тестов)"""
        self._hotel_repo.clear()
        self._room_repo.clear()
        self._booking_repo.clear()
        self._waitlist_repo.clear()
        self._committed = False
        self._rolled_back = False