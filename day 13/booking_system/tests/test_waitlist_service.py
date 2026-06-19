import pytest
from datetime import date, datetime, timedelta

from src.domain.models import BookingStatus
from src.domain.exceptions import (
    RoomNotFoundError, RoomNotAvailableError,
    WaitlistFullError, WaitlistNotFoundError,
    WaitlistExpiredError, BookingConflictError
)
from src.dto.waitlist_dto import WaitlistCreateDTO
from src.dto.booking_dto import BookingCreateDTO


class TestWaitlistService:
    """Тесты сервиса очереди ожидания"""

    def test_add_to_waitlist_success(self, waitlist_service, uow, test_rooms):
        """Успешное добавление в очередь ожидания"""
        # Arrange: создаём бронирование, чтобы номер был занят
        room = test_rooms[0]
        booking_dto = BookingCreateDTO(
            room_id=room.id,
            guest_name="Existing Guest",
            guest_email="existing@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_service.booking_service.create(booking_dto)

        # Act: добавляем в очередь
        dto = WaitlistCreateDTO(
            room_id=room.id,
            guest_name="Waiting Guest",
            guest_email="waiting@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        result = waitlist_service.add_to_waitlist(dto)

        # Assert
        assert result.room_id == room.id
        assert result.guest_email == "waiting@example.com"
        assert result.status == "waiting"

    def test_add_to_waitlist_room_free(self, waitlist_service, uow, test_rooms):
        """Попытка добавиться в очередь, когда номер свободен"""
        room = test_rooms[0]

        dto = WaitlistCreateDTO(
            room_id=room.id,
            guest_name="Waiting Guest",
            guest_email="waiting@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )

        # Act & Assert
        with pytest.raises(RoomNotAvailableError):
            waitlist_service.add_to_waitlist(dto)

    def test_add_to_waitlist_room_not_found(self, waitlist_service, uow):
        """Попытка добавиться в очередь на несуществующий номер"""
        dto = WaitlistCreateDTO(
            room_id=999,
            guest_name="Waiting Guest",
            guest_email="waiting@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )

        with pytest.raises(RoomNotFoundError):
            waitlist_service.add_to_waitlist(dto)

    def test_add_to_waitlist_full(self, waitlist_service, uow, test_rooms):
        """Попытка добавиться в переполненную очередь"""
        room = test_rooms[0]

        # Создаём бронирование
        booking_dto = BookingCreateDTO(
            room_id=room.id,
            guest_name="Existing Guest",
            guest_email="existing@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_service.booking_service.create(booking_dto)

        # Заполняем очередь до предела
        for i in range(waitlist_service.MAX_WAITLIST_SIZE):
            dto = WaitlistCreateDTO(
                room_id=room.id,
                guest_name=f"Guest {i}",
                guest_email=f"guest{i}@example.com",
                check_in=date(2026, 7, 1),
                check_out=date(2026, 7, 5)
            )
            waitlist_service.add_to_waitlist(dto)

        # Пытаемся добавиться в переполненную очередь
        dto = WaitlistCreateDTO(
            room_id=room.id,
            guest_name="Extra Guest",
            guest_email="extra@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )

        with pytest.raises(WaitlistFullError):
            waitlist_service.add_to_waitlist(dto)

    def test_notify_next_in_queue(self, waitlist_service, uow, test_rooms):
        """Уведомление первого в очереди при освобождении номера"""
        room = test_rooms[0]

        # Создаём бронирование
        booking_dto = BookingCreateDTO(
            room_id=room.id,
            guest_name="Existing Guest",
            guest_email="existing@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        booking = waitlist_service.booking_service.create(booking_dto)

        # Добавляем в очередь
        dto = WaitlistCreateDTO(
            room_id=room.id,
            guest_name="Waiting Guest",
            guest_email="waiting@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_entry = waitlist_service.add_to_waitlist(dto)

        # Отменяем бронирование (освобождаем номер)
        waitlist_service.booking_service.cancel(booking.id)

        # Уведомляем первого в очереди
        notification = waitlist_service.notify_next_in_queue(
            room.id,
            date(2026, 7, 1),
            date(2026, 7, 5)
        )

        # Assert
        assert notification is not None
        assert notification.waitlist_id == waitlist_entry.id
        assert notification.guest_email == "waiting@example.com"

        # Проверяем, что запись помечена как уведомлённая
        updated_entry = waitlist_service.waitlist_repo.get_by_id(waitlist_entry.id)
        assert updated_entry.status.value == "notified"
        assert updated_entry.notified_at is not None

    def test_convert_waitlist_to_booking(self, waitlist_service, uow, test_rooms):
        """Конвертация записи из очереди в бронирование"""
        room = test_rooms[0]

        # Создаём бронирование и очередь
        booking_dto = BookingCreateDTO(
            room_id=room.id,
            guest_name="Existing Guest",
            guest_email="existing@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        booking = waitlist_service.booking_service.create(booking_dto)

        dto = WaitlistCreateDTO(
            room_id=room.id,
            guest_name="Waiting Guest",
            guest_email="waiting@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_entry = waitlist_service.add_to_waitlist(dto)

        # Отменяем бронирование и уведомляем
        waitlist_service.booking_service.cancel(booking.id)
        waitlist_service.notify_next_in_queue(room.id, date(2026, 7, 1), date(2026, 7, 5))

        # Конвертируем в бронирование
        new_booking = waitlist_service.convert_waitlist_to_booking(waitlist_entry.id)

        # Assert
        assert new_booking.room_id == room.id
        assert new_booking.guest_name == "Waiting Guest"
        assert new_booking.guest_email == "waiting@example.com"

        # Проверяем, что запись помечена как сконвертированная
        updated_entry = waitlist_service.waitlist_repo.get_by_id(waitlist_entry.id)
        assert updated_entry.status.value == "converted"
        assert updated_entry.converted_at is not None

    def test_convert_waitlist_to_booking_not_notified(self, waitlist_service, uow, test_rooms):
        """Попытка конвертировать запись, которая не была уведомлена"""
        room = test_rooms[0]

        # Создаём бронирование и очередь
        booking_dto = BookingCreateDTO(
            room_id=room.id,
            guest_name="Existing Guest",
            guest_email="existing@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_service.booking_service.create(booking_dto)

        dto = WaitlistCreateDTO(
            room_id=room.id,
            guest_name="Waiting Guest",
            guest_email="waiting@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_entry = waitlist_service.add_to_waitlist(dto)

        # Пытаемся конвертировать без уведомления
        with pytest.raises(Exception) as exc_info:
            waitlist_service.convert_waitlist_to_booking(waitlist_entry.id)

        assert "не была уведомлена" in str(exc_info.value)

    def test_convert_waitlist_to_booking_already_converted(self, waitlist_service, uow, test_rooms):
        """Попытка конвертировать уже сконвертированную запись"""
        room = test_rooms[0]

        # Создаём бронирование, очередь, уведомляем и конвертируем
        booking_dto = BookingCreateDTO(
            room_id=room.id,
            guest_name="Existing Guest",
            guest_email="existing@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        booking = waitlist_service.booking_service.create(booking_dto)

        dto = WaitlistCreateDTO(
            room_id=room.id,
            guest_name="Waiting Guest",
            guest_email="waiting@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_entry = waitlist_service.add_to_waitlist(dto)

        waitlist_service.booking_service.cancel(booking.id)
        waitlist_service.notify_next_in_queue(room.id, date(2026, 7, 1), date(2026, 7, 5))
        waitlist_service.convert_waitlist_to_booking(waitlist_entry.id)

        # Пытаемся конвертировать повторно
        with pytest.raises(Exception) as exc_info:
            waitlist_service.convert_waitlist_to_booking(waitlist_entry.id)

        assert "уже сконвертирована" in str(exc_info.value)

    def test_expire_waitlist_entries(self, waitlist_service, uow, test_rooms):
        """Истечение срока записей в очереди"""
        room = test_rooms[0]

        # Создаём бронирование и очередь
        booking_dto = BookingCreateDTO(
            room_id=room.id,
            guest_name="Existing Guest",
            guest_email="existing@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_service.booking_service.create(booking_dto)

        dto = WaitlistCreateDTO(
            room_id=room.id,
            guest_name="Waiting Guest",
            guest_email="waiting@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_entry = waitlist_service.add_to_waitlist(dto)

        # Изменяем время создания записи (делаем старой)
        entry = waitlist_service.waitlist_repo.get_by_id(waitlist_entry.id)
        entry.created_at = datetime.now() - timedelta(hours=25)
        waitlist_service.waitlist_repo.update(entry)
        waitlist_service.uow.commit()

        # Истечение записей
        expired_ids = waitlist_service.expire_waitlist_entries(max_wait_hours=24)

        # Assert
        assert len(expired_ids) == 1
        assert expired_ids[0] == waitlist_entry.id

        updated_entry = waitlist_service.waitlist_repo.get_by_id(waitlist_entry.id)
        assert updated_entry.status.value == "expired"

    def test_get_waitlist_by_room(self, waitlist_service, uow, test_rooms):
        """Получение очереди ожидания по номеру"""
        room = test_rooms[0]

        # Создаём бронирование
        booking_dto = BookingCreateDTO(
            room_id=room.id,
            guest_name="Existing Guest",
            guest_email="existing@example.com",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5)
        )
        waitlist_service.booking_service.create(booking_dto)

        # Добавляем несколько записей в очередь
        for i in range(3):
            dto = WaitlistCreateDTO(
                room_id=room.id,
                guest_name=f"Guest {i}",
                guest_email=f"guest{i}@example.com",
                check_in=date(2026, 7, 1),
                check_out=date(2026, 7, 5)
            )
            waitlist_service.add_to_waitlist(dto)

        # Получаем очередь
        entries = waitlist_service.get_waitlist_by_room(room.id)

        # Assert
        assert len(entries) == 3
        assert all(e.room_id == room.id for e in entries)
        assert entries[0].guest_name == "Guest 0"  # Проверка порядка (FIFO)