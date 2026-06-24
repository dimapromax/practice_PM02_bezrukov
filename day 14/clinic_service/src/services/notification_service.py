import logging
from datetime import datetime
from typing import List
from src.domain.entities import Notification

logger = logging.getLogger(__name__)

class NotificationService:
    """Сервис для отправки уведомлений (имитация через логирование)"""
    
    def __init__(self):
        self._notifications: List[Notification] = []
    
    def send_sms(self, phone: str, message: str) -> bool:
        """Отправка SMS-уведомления"""
        notification = Notification(recipient=phone, message=message, sent=True)
        self._notifications.append(notification)
        logger.info(f"📱 SMS отправлено на {phone}: {message}")
        return True
    
    def send_email(self, email: str, message: str) -> bool:
        """Отправка Email-уведомления"""
        notification = Notification(recipient=email, message=message, sent=True)
        self._notifications.append(notification)
        logger.info(f"📧 Email отправлен на {email}: {message}")
        return True
    
    def send_appointment_reminder(self, phone: str, doctor_name: str, appointment_date: str, appointment_time: str):
        """Отправка напоминания о записи к врачу"""
        message = f"Напоминаем о записи к врачу {doctor_name} на {appointment_date} в {appointment_time}"
        return self.send_sms(phone, message)
    
    def send_cancellation_confirmation(self, phone: str, appointment_date: str, appointment_time: str):
        """Подтверждение отмены записи"""
        message = f"Запись на {appointment_date} в {appointment_time} успешно отменена"
        return self.send_sms(phone, message)
    
    def get_notifications(self) -> List[Notification]:
        """Получить все отправленные уведомления (для тестирования)"""
        return self._notifications