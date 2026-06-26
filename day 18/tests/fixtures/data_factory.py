import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.core.domain import Transaction, PaymentMethod, PaymentStatus


class DataFactory:
    """Фабрика тестовых данных"""
    
    @staticmethod
    def create_transaction(
        amount: float = None,
        method: str = None,
        status: str = None
    ) -> Transaction:
        """Создать транзакцию для тестов"""
        if amount is None:
            amount = random.uniform(10.0, 10000.0)
        
        if method is None:
            method = random.choice(["card", "cash", "online"])
        
        tx = Transaction(
            amount=amount,
            method=PaymentMethod(method)
        )
        
        if status == "completed":
            tx.complete()
        elif status == "failed":
            tx.fail()
        elif status == "refunded":
            tx.complete()
            tx.refund()
        
        return tx
    
    @staticmethod
    def create_test_data(size: int = 10) -> List[Dict[str, Any]]:
        """Создать тестовые данные"""
        data = []
        now = datetime.now()
        
        for i in range(size):
            data.append({
                'id': f"TXN-{i+1:03d}",
                'amount': random.uniform(10.0, 10000.0),
                'method': random.choice(['card', 'cash', 'online']),
                'status': random.choice(['pending', 'completed', 'failed', 'refunded']),
                'created_at': now - timedelta(days=random.randint(0, 30))
            })
        
        return data