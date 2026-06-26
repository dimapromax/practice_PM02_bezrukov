import pytest
from datetime import datetime

from src.infrastructure.repositories import InMemoryPaymentRepository
from src.core.domain import Transaction, Refund, PaymentMethod, PaymentStatus


class TestPaymentRepository:
    """Тесты для репозитория платежей"""
    
    @pytest.fixture
    def repo(self):
        return InMemoryPaymentRepository()
    
    def test_add_transaction(self, repo):
        """Добавление транзакции"""
        tx = Transaction(amount=1000.0, method=PaymentMethod.CARD)
        result = repo.add_transaction(tx)
        
        assert result.id == tx.id
        assert repo.get_transaction(tx.id) is not None
    
    def test_get_transaction(self, repo):
        """Получение транзакции"""
        tx = Transaction(amount=1000.0, method=PaymentMethod.CARD)
        repo.add_transaction(tx)
        
        result = repo.get_transaction(tx.id)
        assert result is not None
        assert result.amount == 1000.0
    
    def test_get_transaction_not_found(self, repo):
        """Получение несуществующей транзакции"""
        result = repo.get_transaction("INVALID")
        assert result is None
    
    def test_get_all_transactions(self, repo):
        """Получение всех транзакций"""
        for i in range(3):
            tx = Transaction(amount=float(1000 * (i + 1)), method=PaymentMethod.CARD)
            repo.add_transaction(tx)
        
        results = repo.get_all_transactions()
        assert len(results) == 3
    
    def test_add_refund(self, repo):
        """Добавление возврата"""
        refund = Refund(
            transaction_id="TXN-001",
            original_amount=1000.0,
            refund_amount=850.0,
            fee=150.0,
            days_before=3
        )
        result = repo.add_refund(refund)
        
        assert result.id == refund.id
        assert repo.get_refund(refund.id) is not None
    
    def test_get_refund(self, repo):
        """Получение возврата"""
        refund = Refund(
            transaction_id="TXN-001",
            original_amount=1000.0,
            refund_amount=850.0,
            fee=150.0,
            days_before=3
        )
        repo.add_refund(refund)
        
        result = repo.get_refund(refund.id)
        assert result is not None
        assert result.refund_amount == 850.0
    
    def test_get_refund_not_found(self, repo):
        """Получение несуществующего возврата"""
        result = repo.get_refund("INVALID")
        assert result is None
    
    def test_clear(self, repo):
        """Очистка репозитория"""
        tx = Transaction(amount=1000.0, method=PaymentMethod.CARD)
        repo.add_transaction(tx)
        assert len(repo.get_all_transactions()) == 1
        
        repo.clear()
        assert len(repo.get_all_transactions()) == 0