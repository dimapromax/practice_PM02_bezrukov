from datetime import date, datetime
from typing import List, Optional

from src.domain.models import Booking, BookingStatus, Room
from src.domain.exceptions import (
    RoomNotFoundError, BookingNotFoundError,
    BookingConflictError, InvalidDatesError,
    DomainError, BookingStatusTransitionError
)
from src.dto.booking_dto import BookingCreateDTO, BookingResponseDTO, BookingUpdateDTO
from src.uow.unit_of_work import UnitOfWork
from src.services.pricing_service import PricingService


class BookingService:
 

    def __init__(self, uow: UnitOfWork, pricing_service: PricingService):
        self.uow = uow
        self.pricing_service = pricing_service
        self.booking_repo = uow.bookings
        self.room_repo = uow.rooms

    def create(self, dto: BookingCreateDTO) -> BookingResponseDTO:
   
        # 1. Проверяем существование номера
        room = self.room_repo.get_by_id(dto.room_id)
        if not room:
            raise RoomNotFoundError(f"Номер {dto.room_id} не найден")

        if not room.is_active:
            raise RoomNotFoundError(f"Номер {dto.room_id} не активен")

        # 2. Проверяем пересечения бронирований
        existing = self.booking_repo.get_by_room_and_dates(
            dto.room_id, dto.check_in, dto.check_out
        )
        if existing:
            raise BookingConflictError(
                f"Номер {dto.room_id} уже забронирован на эти даты",
                details={"conflicting_bookings": [b.id for b in existing]}
            )

        # 3. Рассчитываем стоимость
        total_price = self.pricing_service.calculate_price(
            room, dto.check_in, dto.check_out
        )

        # 4. Создаём бронирование
        booking = Booking(
            id=None,
            room_id=dto.room_id,
            guest_name=dto.guest_name,
            guest_email=dto.guest_email,
            check_in=dto.check_in,
            check_out=dto.check_out,
            total_price=total_price,
            status=BookingStatus.PENDING
        )

        # 5. Сохраняем
        saved = self.booking_repo.add(booking)
        self.uow.commit()

        return BookingResponseDTO.from_orm(saved)

    def cancel(self, booking_id: int) -> bool:
      
  
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Бронирование {booking_id} не найдено")

        if booking.status in (BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT):
            raise DomainError(
                f"Нельзя отменить бронирование в статусе {booking.status.value}"
            )

        # Отмена бронирования
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now()

        self.booking_repo.update(booking)
        self.uow.commit()

        return True

    def get_available_rooms(
        self,
        hotel_id: int,
        check_in: date,
        check_out: date,
        capacity: Optional[int] = None,
        room_type: Optional[str] = None
    ) -> List[dict]:
  
        # 1. Получаем все номера отеля
        rooms = self.room_repo.get_by_hotel(hotel_id, active_only=True)

        # 2. Фильтруем по вместимости
        if capacity:
            rooms = [r for r in rooms if r.capacity >= capacity]

        # 3. Фильтруем по типу номера
        if room_type:
            rooms = [r for r in rooms if r.room_type == room_type]

        # 4. Для каждого номера проверяем доступность
        available = []
        for room in rooms:
            existing = self.booking_repo.get_by_room_and_dates(
                room.id, check_in, check_out
            )
            if not existing:
                available.append({
                    'room_id': room.id,
                    'number': room.number,
                    'capacity': room.capacity,
                    'room_type': room.room_type,
                    'price_per_night': room.price_per_night
                })

        return available

    def confirm(self, booking_id: int) -> None:
        """Подтвердить бронирование (администратор)"""
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Бронирование {booking_id} не найдено")

        if booking.status != BookingStatus.PENDING:
            raise BookingStatusTransitionError(
                f"Бронирование в статусе {booking.status.value} нельзя подтвердить"
            )

        booking.status = BookingStatus.CONFIRMED
        self.booking_repo.update(booking)
        self.uow.commit()

    def check_in(self, booking_id: int) -> None:
        """Заселить гостя"""
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Бронирование {booking_id} не найдено")

        if booking.status != BookingStatus.CONFIRMED:
            raise BookingStatusTransitionError(
                f"Нельзя заселить бронирование в статусе {booking.status.value}"
            )

        booking.status = BookingStatus.CHECKED_IN
        self.booking_repo.update(booking)
        self.uow.commit()

    def check_out(self, booking_id: int) -> None:
        """Выселить гостя"""
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Бронирование {booking_id} не найдено")

        if booking.status != BookingStatus.CHECKED_IN:
            raise BookingStatusTransitionError(
                f"Нельзя выселить бронирование в статусе {booking.status.value}"
            )

        booking.status = BookingStatus.CHECKED_OUT
        self.booking_repo.update(booking)
        self.uow.commit()

    def get_by_id(self, booking_id: int) -> Optional[BookingResponseDTO]:
        """Получить бронирование по ID"""
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            return None
        return BookingResponseDTO.from_orm(booking)

    def get_by_guest(self, guest_email: str) -> List[BookingResponseDTO]:
        """Получить бронирования гостя по email"""
        bookings = self.booking_repo.get_all(guest_email=guest_email)
        return [BookingResponseDTO.from_orm(b) for b in bookings]

    def get_all(self) -> List[BookingResponseDTO]:
        """Получить все бронирования"""
        bookings = self.booking_repo.get_all()
        return [BookingResponseDTO.from_orm(b) for b in bookings]

    def update(self, booking_id: int, dto: BookingUpdateDTO) -> Optional[BookingResponseDTO]:
        """Обновить бронирование"""
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            return None

        if dto.guest_name:
            booking.guest_name = dto.guest_name
        if dto.guest_email:
            booking.guest_email = dto.guest_email

        # Обновление дат требует повторной проверки доступности
        if dto.check_in or dto.check_out:
            new_check_in = dto.check_in or booking.check_in
            new_check_out = dto.check_out or booking.check_out

            # Проверяем, что номер всё ещё доступен на новые даты
            existing = self.booking_repo.get_by_room_and_dates(
                booking.room_id, new_check_in, new_check_out
            )
            # Исключаем текущее бронирование из проверки
            existing = [b for b in existing if b.id != booking_id]

            if existing:
                raise BookingConflictError(
                    f"Номер {booking.room_id} занят на новые даты"
                )

            booking.check_in = new_check_in
            booking.check_out = new_check_out

            # Пересчитываем стоимость
            room = self.room_repo.get_by_id(booking.room_id)
            if room:
                booking.total_price = self.pricing_service.calculate_price(
                    room, booking.check_in, booking.check_out
                )

        self.booking_repo.update(booking)
        self.uow.commit()

        return BookingResponseDTO.from_orm(booking)