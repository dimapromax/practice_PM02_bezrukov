from abc import ABC, abstractmethod
from typing import List, Callable

from src.dto.waitlist_dto import WaitlistNotificationDTO


class WaitlistObserver(ABC):
    """Абстрактный наблюдатель для очереди ожидания"""

    @abstractmethod
    def on_room_available(self, notification: WaitlistNotificationDTO) -> None:
        """Вызывается при освобождении номера"""
        pass


class EmailWaitlistObserver(WaitlistObserver):
    """Наблюдатель для отправки email-уведомлений"""

    def __init__(self, send_email_func: Callable):
        """
        Args:
            send_email_func: Функция для отправки email
        """
        self.send_email = send_email_func

    def on_room_available(self, notification: WaitlistNotificationDTO) -> None:
        """Отправить email-уведомление пользователю"""
        subject = f"Номер {notification.available_room_number} освободился!"
        body = f"""
        Уважаемый(ая) {notification.guest_name}!

        Номер {notification.available_room_number} освободился на даты:
        Заезд: {notification.check_in}
        Выезд: {notification.check_out}

        Вы можете забронировать его сейчас.

        Ссылка для бронирования: https://bookly.example.com/booking/confirm/{notification.waitlist_id}

        С уважением,
        Команда Bookly
        """

        self.send_email(
            to_email=notification.guest_email,
            subject=subject,
            body=body
        )


class SMSWaitlistObserver(WaitlistObserver):
    """Наблюдатель для отправки SMS-уведомлений"""

    def __init__(self, send_sms_func: Callable):
        """
        Args:
            send_sms_func: Функция для отправки SMS
        """
        self.send_sms = send_sms_func

    def on_room_available(self, notification: WaitlistNotificationDTO) -> None:
        """Отправить SMS-уведомление пользователю"""
        message = (
            f"Номер {notification.available_room_number} освободился! "
            f"Забронируйте сейчас: https://bookly.example.com/waitlist/{notification.waitlist_id}"
        )

        self.send_sms(
            phone_number=notification.guest_email,  # В реальном проекте здесь был бы номер телефона
            message=message
        )


class WaitlistNotifier:

    def __init__(self):
        self._observers: List[WaitlistObserver] = []

    def attach(self, observer: WaitlistObserver) -> None:
        """Добавить наблюдателя"""
        self._observers.append(observer)

    def detach(self, observer: WaitlistObserver) -> None:
        """Удалить наблюдателя"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, notification: WaitlistNotificationDTO) -> None:
        """Уведомить всех наблюдателей"""
        for observer in self._observers:
            observer.on_room_available(notification)