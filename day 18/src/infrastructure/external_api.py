import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import random

from src.application.interfaces import ExternalPaymentGateway
from src.core.exceptions import PaymentError

logger = logging.getLogger(__name__)


class MockPaymentGateway(ExternalPaymentGateway):
    """
    Mock-реализация платежного шлюза для тестирования.
    В реальном проекте здесь был бы Stripe, YooKassa, Tinkoff и т.д.
    """
    
    def __init__(self):
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._should_fail = False
    
    def set_fail_mode(self, enabled: bool) -> None:
        """Включить режим ошибок для тестирования"""
        self._should_fail = enabled
    
    def charge(self, amount: float, card_number: str, currency: str = "RUB") -> dict:
        """Списать средства"""
        logger.info(f"Processing payment: {amount} {currency}, card: {card_number[:4]}****")
        
        # Имитация ошибки
        if self._should_fail:
            raise PaymentError("Payment gateway unavailable")
        
        # Имитация случайной ошибки (5%)
        if random.random() < 0.05:
            raise PaymentError("Random payment error")
        
        # Проверка формата карты (для демонстрации)
        if len(card_number.replace(' ', '')) < 13:
            raise PaymentError("Invalid card number")
        
        transaction_id = f"GW-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        
        result = {
            'success': True,
            'transaction_id': transaction_id,
            'amount': amount,
            'currency': currency,
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'card_last4': card_number[-4:] if len(card_number) >= 4 else '****'
        }
        
        self._transactions[transaction_id] = result
        return result
    
    def refund(self, transaction_id: str, amount: float) -> dict:
        """Вернуть средства"""
        logger.info(f"Processing refund: {transaction_id}, amount: {amount}")
        
        # Проверка существования транзакции
        if transaction_id not in self._transactions:
            return {
                'success': False,
                'error': 'Transaction not found',
                'transaction_id': transaction_id
            }
        
        # Имитация ошибки
        if self._should_fail:
            raise PaymentError("Refund gateway unavailable")
        
        result = {
            'success': True,
            'transaction_id': f"REF-{transaction_id}",
            'original_transaction_id': transaction_id,
            'amount': amount,
            'status': 'completed',
            'timestamp': datetime.now().isoformat()
        }
        
        # Обновление статуса оригинальной транзакции
        if transaction_id in self._transactions:
            self._transactions[transaction_id]['status'] = 'refunded'
        
        return result
    
    def get_status(self, transaction_id: str) -> str:
        """Получить статус транзакции"""
        if transaction_id in self._transactions:
            return self._transactions[transaction_id].get('status', 'unknown')
        return 'not_found'
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о транзакции"""
        return self._transactions.get(transaction_id)


class NotificationService:
    """Сервис уведомлений"""
    
    def __init__(self):
        self._sent_emails: list = []
        self._sent_sms: list = []
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Отправить email (Mock)"""
        logger.info(f"Sending email to {to}: {subject}")
        self._sent_emails.append({
            'to': to,
            'subject': subject,
            'body': body,
            'sent_at': datetime.now().isoformat()
        })
        
        # Имитация ошибки (2%)
        if random.random() < 0.02:
            logger.warning(f"Failed to send email to {to}")
            return False
        
        return True
    
    def send_sms(self, phone: str, message: str) -> bool:
        """Отправить SMS (Mock)"""
        logger.info(f"Sending SMS to {phone}: {message[:50]}...")
        self._sent_sms.append({
            'phone': phone,
            'message': message,
            'sent_at': datetime.now().isoformat()
        })
        
        # Имитация ошибки (2%)
        if random.random() < 0.02:
            logger.warning(f"Failed to send SMS to {phone}")
            return False
        
        return True
    
    def get_sent_emails(self) -> list:
        """Получить список отправленных email"""
        return self._sent_emails
    
    def get_sent_sms(self) -> list:
        """Получить список отправленных SMS"""
        return self._sent_sms
    
    def clear(self) -> None:
        """Очистить историю уведомлений"""
        self._sent_emails.clear()
        self._sent_sms.clear()