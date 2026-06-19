from datetime import datetime, date
from typing import List, Optional

from src.domain.models import WaitlistEntry, WaitlistStatus, Booking, BookingStatus
from src.domain.exceptions import (
    RoomNotFoundError, BookingConflictError, WaitlistNotFoundError,
    WaitlistFullError, WaitlistExpiredError, WaitlistAlreadyNotifiedError,
    WaitlistConvertError, RoomNotAvailableError
)
from src.dto.waitlist_dto import WaitlistCreateDTO, WaitlistResponseDTO, WaitlistNotificationDTO
from src.dto.booking_dto import BookingCreateDTO
from src.uow.unit_of_work import UnitOfWork
from src.services.pricing_service import PricingService
from src.services.booking_service import BookingService


class WaitlistService:
   

    MAX_WAITLIST_SIZE = 10  # Максимальный размер очереди на номер

    def __init__(self, uow: UnitOfWork, booking_service: BookingService):
        self.uow = uow
        self.booking_service = booking_service
        self.waitlist_repo = uow.waitlist
        self.booking_repo = uow.bookings
        self.room_repo = uow.rooms

    def add_to_waitlist(self, dto: WaitlistCreateDTO) -> WaitlistResponseDTO:
 
        # 1. Проверяем существование номера
        room = self.room_repo.get_by_id(dto.room_id)
        if not room:
            raise RoomNotFoundError(f"Номер {dto.room_id} не найден")

        if not room.is_active:
            raise RoomNotFoundError(f"Номер {dto.room_id} не активен")

        # 2. Проверяем, что номер действительно занят на эти даты
        existing_bookings = self.booking_repo.get_by_room_and_dates(
            dto.room_id, dto.check_in, dto.check_out
        )

        if not existing_bookings:
            # Если номер свободен — предлагаем забронировать
            raise RoomNotAvailableError(
                f"Номер {dto.room_id} свободен на указанные даты. "
                "Пожалуйста, создайте бронирование напрямую."
            )

        # 3. Проверяем размер очереди
        waiting_entries = self.waitlist_repo.get_waiting_by_room_and_dates(
            dto.room_id, dto.check_in, dto.check_out
        )
        if len(waiting_entries) >= self.MAX_WAITLIST_SIZE:
            raise WaitlistFullError(
                f"Очередь ожидания на номер {dto.room_id} переполнена "
                f"(максимум {self.MAX_WAITLIST_SIZE} записей)"
            )

        # 4. Проверяем, не записан ли уже пользователь в очередь
        existing_entry = self._find_user_in_waitlist(
            dto.room_id, dto.guest_email, dto.check_in, dto.check_out
        )
        if existing_entry:
            return WaitlistResponseDTO.from_orm(existing_entry)

        # 5. Создаём запись в очереди
        entry = WaitlistEntry(
            id=None,
            room_id=dto.room_id,
            guest_name=dto.guest_name,
            guest_email=dto.guest_email,
            check_in=dto.check_in,
            check_out=dto.check_out,
            desired_room_type=dto.desired_room_type or room.room_type,
            status=WaitlistStatus.WAITING
        )

        saved = self.waitlist_repo.add(entry)
        self.uow.commit()

        return WaitlistResponseDTO.from_orm(saved)

    def _find_user_in_waitlist(
        self,
        room_id: int,
        guest_email: str,
        check_in: date,
        check_out: date
    ) -> Optional[WaitlistEntry]:
        """Найти активную запись пользователя в очереди"""
        for entry in self.waitlist_repo.get_waiting_by_room_and_dates(room_id, check_in, check_out):
            if entry.guest_email == guest_email:
                return entry
        return None

    def notify_next_in_queue(
        self,
        room_id: int,
        check_in: date,
        check_out: date
    ) -> Optional[WaitlistNotificationDTO]:
        """
        Уведомить первого в очереди при освобождении номера.
        Вызывается при отмене бронирования.
        """
        # 1. Находим первого в очереди (FIFO)
        waiting_entries = self.waitlist_repo.get_waiting_by_room_and_dates(
            room_id, check_in, check_out
        )

        # Сортируем по времени создания (FIFO)
        waiting_entries.sort(key=lambda e: e.created_at)

        if not waiting_entries:
            return None

        next_entry = waiting_entries[0]

        # 2. Отмечаем, что пользователь уведомлён
        next_entry.status = WaitlistStatus.NOTIFIED
        next_entry.notified_at = datetime.now()
        self.waitlist_repo.update(next_entry)
        self.uow.commit()

        # 3. Формируем уведомление
        room = self.room_repo.get_by_id(room_id)

        return WaitlistNotificationDTO(
            waitlist_id=next_entry.id,
            room_id=room_id,
            guest_name=next_entry.guest_name,
            guest_email=next_entry.guest_email,
            check_in=next_entry.check_in,
            check_out=next_entry.check_out,
            available_room_id=room_id,
            available_room_number=room.number if room else "N/A"
        )

    def convert_waitlist_to_booking(self, waitlist_id: int) -> Booking:
        """
        Конвертировать запись из очереди в бронирование.
        Пользователь получил уведомление и теперь может забронировать номер.
        """
        # 1. Получаем запись из очереди
        entry = self.waitlist_repo.get_by_id(waitlist_id)
        if not entry:
            raise WaitlistNotFoundError(f"Запись в очереди {waitlist_id} не найдена")

        if entry.status == WaitlistStatus.EXPIRED:
            raise WaitlistExpiredError(f"Запись в очереди {waitlist_id} истекла")

        if entry.status == WaitlistStatus.CONVERTED:
            raise WaitlistConvertError(f"Запись в очереди {waitlist_id} уже сконвертирована")

        if entry.status != WaitlistStatus.NOTIFIED:
            raise WaitlistAlreadyNotifiedError(
                f"Запись в очереди {waitlist_id} ещё не была уведомлена"
            )

        # 2. Проверяем, что номер всё ещё свободен
        existing_bookings = self.booking_repo.get_by_room_and_dates(
            entry.room_id, entry.check_in, entry.check_out
        )
        if existing_bookings:
            raise BookingConflictError(
                f"Номер {entry.room_id} снова занят на указанные даты. "
                "Возможно, кто-то успел забронировать."
            )

        # 3. Создаём бронирование
        booking_dto = BookingCreateDTO(
            room_id=entry.room_id,
            guest_name=entry.guest_name,
            guest_email=entry.guest_email,
            check_in=entry.check_in,
            check_out=entry.check_out
        )

        booking = self.booking_service.create(booking_dto)

        # 4. Отмечаем запись как сконвертированную
        entry.status = WaitlistStatus.CONVERTED
        entry.converted_at = datetime.now()
        self.waitlist_repo.update(entry)
        self.uow.commit()

        return booking

    def expire_waitlist_entries(self, max_wait_hours: int = 24) -> List[int]:
        """
        Отметить истекшие записи в очереди.
        Возвращает список ID истекших записей.
        """
        expired = self.waitlist_repo.get_expired_entries(max_wait_hours)
        expired_ids = []

        for entry in expired:
            entry.status = WaitlistStatus.EXPIRED
            self.waitlist_repo.update(entry)
            expired_ids.append(entry.id)

        self.uow.commit()
        return expired_ids

    def get_waitlist_by_room(self, room_id: int) -> List[WaitlistResponseDTO]:
        """Получить всю очередь ожидания для номера"""
        entries = self.waitlist_repo.get_all(room_id=room_id)
        return [WaitlistResponseDTO.from_orm(e) for e in entries]

    def get_waiting_count_by_room(
        self,
        room_id: int,
        check_in: date,
        check_out: date
    ) -> int:
        """Получить количество ожидающих для номера и дат"""
        return len(self.waitlist_repo.get_waiting_by_room_and_dates(room_id, check_in, check_out))