import pytest
from datetime import datetime

from src.core.domain import Transaction, Payment, Refund, PaymentStatus, PaymentMethod


class TestTransaction:
    """Тесты для Transaction"""
    
    def test_transaction_creation(self):
        """Создание транзакции"""
        tx = Transaction(amount=1000.0, method=PaymentMethod.CARD)
        assert tx.amount == 1000.0
        assert tx.method == PaymentMethod.CARD
        assert tx.status == PaymentStatus.PENDING
    
    def test_transaction_complete(self):
        """Завершение транзакции"""
        tx = Transaction()
        tx.complete()
        assert tx.status == PaymentStatus.COMPLETED
    
    def test_transaction_fail(self):
        """Неудачная транзакция"""
        tx = Transaction()
        tx.fail()
        assert tx.status == PaymentStatus.FAILED
    
    def test_transaction_refund(self):
        """Возврат транзакции"""
        tx = Transaction()
        tx.refund()
        assert tx.status == PaymentStatus.REFUNDED


class TestRefund:
    """Тесты для Refund"""
    
    def test_refund_creation(self):
        """Создание возврата"""
        refund = Refund(
            transaction_id="TXN-001",
            original_amount=1000.0,
            refund_amount=850.0,
            fee=150.0,
            days_before=3
        )
        assert refund.transaction_id == "TXN-001"
        assert refund.original_amount == 1000.0
        assert refund.refund_amount == 850.0
        assert refund.fee == 150.0
        assert refund.days_before == 3