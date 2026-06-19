class DomainError(Exception):
    """Базовое исключение домена"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


# === Ошибки отелей ===
class HotelNotFoundError(DomainError):
    """Отель не найден"""
    pass


# === Ошибки номеров ===
class RoomNotFoundError(DomainError):
    """Номер не найден"""
    pass


class RoomNotAvailableError(DomainError):
    """Номер недоступен"""
    pass


class RoomTypeNotFoundError(DomainError):
    """Тип номера не найден"""
    pass


# === Ошибки бронирований ===
class BookingNotFoundError(DomainError):
    """Бронирование не найдено"""
    pass


class BookingConflictError(DomainError):
    """Конфликт бронирований (пересечение дат)"""
    pass


class InvalidDatesError(DomainError):
    """Некорректные даты"""
    pass


class BookingStatusTransitionError(DomainError):
    """Некорректный переход статуса"""
    pass


# === Ошибки очереди ожидания ===
class WaitlistNotFoundError(DomainError):
    """Запись в очереди ожидания не найдена"""
    pass


class WaitlistFullError(DomainError):
    """Очередь ожидания переполнена"""
    pass


class WaitlistExpiredError(DomainError):
    """Запись в очереди ожидания истекла"""
    pass


class WaitlistAlreadyNotifiedError(DomainError):
    """Запись уже была уведомлена"""
    pass


class WaitlistConvertError(DomainError):
    """Ошибка конвертации ожидания в бронирование"""
    pass