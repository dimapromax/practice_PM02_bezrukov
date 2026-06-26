from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class PaymentStatus(Enum):
    """Статусы платежа"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    """Методы оплаты"""
    CARD = "card"
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"


@dataclass
class Transaction:
    """Транзакция платежа"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    amount: float = 0.0
    method: PaymentMethod = PaymentMethod.CARD
    commission: float = 0.0
    net_amount: float = 0.0
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def complete(self) -> None:
        """Завершить транзакцию"""
        self.status = PaymentStatus.COMPLETED
        self.updated_at = datetime.now()

    def fail(self) -> None:
        """Отметить транзакцию как неудачную"""
        self.status = PaymentStatus.FAILED
        self.updated_at = datetime.now()

    def refund(self) -> None:
        """Отметить транзакцию как возвращенную"""
        self.status = PaymentStatus.REFUNDED
        self.updated_at = datetime.now()


@dataclass
class Refund:
    """Возврат средств"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    transaction_id: str = ""
    original_amount: float = 0.0
    refund_amount: float = 0.0
    fee: float = 0.0
    days_before: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    reason: str = ""


@dataclass
class Payment:
    """Платеж"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    amount: float = 0.0
    method: PaymentMethod = PaymentMethod.CARD
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)