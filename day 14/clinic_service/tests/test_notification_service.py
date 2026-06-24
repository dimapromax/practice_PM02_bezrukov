import pytest
from datetime import datetime
from src.services.notification_service import NotificationService

def test_send_sms_success():
    """Тест отправки SMS"""
    service = NotificationService()
    result = service.send_sms("+79001234567", "Тестовое сообщение")
    
    assert result is True
    assert len(service.get_notifications()) == 1
    notification = service.get_notifications()[0]
    assert notification.recipient == "+79001234567"
    assert notification.message == "Тестовое сообщение"
    assert notification.sent is True

def test_send_email_success():
    """Тест отправки Email"""
    service = NotificationService()
    result = service.send_email("test@mail.ru", "Тестовое письмо")
    
    assert result is True
    assert len(service.get_notifications()) == 1
    notification = service.get_notifications()[0]
    assert notification.recipient == "test@mail.ru"
    assert notification.message == "Тестовое письмо"

def test_send_appointment_reminder():
    """Тест отправки напоминания о записи"""
    service = NotificationService()
    result = service.send_appointment_reminder(
        "+79001234567",
        "Иван Иванов",
        "15.01.2026",
        "10:00"
    )
    
    assert result is True
    assert "напоминаем" in service.get_notifications()[0].message.lower()
    assert "Иван Иванов" in service.get_notifications()[0].message

def test_multiple_notifications():
    """Тест отправки нескольких уведомлений"""
    service = NotificationService()
    
    service.send_sms("+79001234567", "Сообщение 1")
    service.send_email("test@mail.ru", "Сообщение 2")
    service.send_sms("+79007654321", "Сообщение 3")
    
    assert len(service.get_notifications()) == 3