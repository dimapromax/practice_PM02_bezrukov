from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.domain import Transaction, Refund


class PaymentRepository(ABC):
    """Абстрактный репозиторий платежей"""
    
    @abstractmethod
    def add_transaction(self, transaction: Transaction) -> Transaction:
        pass
    
    @abstractmethod
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        pass
    
    @abstractmethod
    def get_all_transactions(self) -> List[Transaction]:
        pass
    
    @abstractmethod
    def add_refund(self, refund: Refund) -> Refund:
        pass
    
    @abstractmethod
    def get_refund(self, refund_id: str) -> Optional[Refund]:
        pass


class InMemoryPaymentRepository(PaymentRepository):
    """In-Memory реализация репозитория платежей"""
    
    def __init__(self):
        self._transactions: dict[str, Transaction] = {}
        self._refunds: dict[str, Refund] = {}
    
    def add_transaction(self, transaction: Transaction) -> Transaction:
        self._transactions[transaction.id] = transaction
        return transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        return self._transactions.get(transaction_id)
    
    def get_all_transactions(self) -> List[Transaction]:
        return list(self._transactions.values())
    
    def add_refund(self, refund: Refund) -> Refund:
        self._refunds[refund.id] = refund
        return refund
    
    def get_refund(self, refund_id: str) -> Optional[Refund]:
        return self._refunds.get(refund_id)
    
    def clear(self):
        """Очистка хранилища (для тестов)"""
        self._transactions.clear()
        self._refunds.clear()