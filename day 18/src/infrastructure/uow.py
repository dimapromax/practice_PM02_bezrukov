from contextlib import contextmanager
from typing import Type

from src.infrastructure.repositories import PaymentRepository, InMemoryPaymentRepository


class UnitOfWork:
    """Unit of Work для управления транзакциями"""
    
    def __init__(self):
        self._payment_repo = InMemoryPaymentRepository()
        self._committed = False
    
    @property
    def payments(self) -> PaymentRepository:
        return self._payment_repo
    
    def commit(self) -> None:
        """Фиксация транзакции"""
        self._committed = True
    
    def rollback(self) -> None:
        """Откат транзакции"""
        self._committed = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        elif not self._committed:
            self.commit()