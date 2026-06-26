from abc import ABC, abstractmethod
from typing import Optional, List, Protocol

from src.core.domain import Transaction, Refund


class PaymentRepository(ABC):
    """Интерфейс репозитория платежей"""
    
    @abstractmethod
    def add_transaction(self, transaction: Transaction) -> Transaction:
        """Сохранить транзакцию"""
        pass
    
    @abstractmethod
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Получить транзакцию по ID"""
        pass
    
    @abstractmethod
    def get_all_transactions(self) -> List[Transaction]:
        """Получить все транзакции"""
        pass
    
    @abstractmethod
    def add_refund(self, refund: Refund) -> Refund:
        """Сохранить возврат"""
        pass
    
    @abstractmethod
    def get_refund(self, refund_id: str) -> Optional[Refund]:
        """Получить возврат по ID"""
        pass


class ExternalPaymentGateway(ABC):
    """Интерфейс внешнего платежного шлюза"""
    
    @abstractmethod
    def charge(self, amount: float, card_number: str, currency: str = "RUB") -> dict:
        """Списать средства"""
        pass
    
    @abstractmethod
    def refund(self, transaction_id: str, amount: float) -> dict:
        """Вернуть средства"""
        pass
    
    @abstractmethod
    def get_status(self, transaction_id: str) -> str:
        """Получить статус транзакции"""
        pass


class NotificationService(ABC):
    """Интерфейс сервиса уведомлений"""
    
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Отправить email"""
        pass
    
    @abstractmethod
    def send_sms(self, phone: str, message: str) -> bool:
        """Отправить SMS"""
        pass