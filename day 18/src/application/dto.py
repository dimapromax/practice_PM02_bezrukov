from dataclasses import dataclass
from typing import Optional
from enum import Enum


class PaymentMethodDTO(str, Enum):
    """DTO для методов оплаты"""
    CARD = "card"
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"


class PaymentStatusDTO(str, Enum):
    """DTO для статусов платежа"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


@dataclass
class PaymentRequestDTO:
    """DTO для запроса на платеж"""
    amount: float
    method: str = "card"
    metadata: Optional[dict] = None


@dataclass
class PaymentResponseDTO:
    """DTO для ответа платежа"""
    success: bool
    transaction_id: Optional[str] = None
    amount: float = 0.0
    commission: float = 0.0
    net_amount: float = 0.0
    status: str = "pending"
    error: Optional[str] = None


@dataclass
class RefundRequestDTO:
    """DTO для запроса на возврат"""
    transaction_id: str
    original_amount: float
    days_before: int


@dataclass
class RefundResponseDTO:
    """DTO для ответа на возврат"""
    success: bool
    refund_amount: float = 0.0
    fee: float = 0.0
    error: Optional[str] = None


@dataclass
class CommissionRequestDTO:
    """DTO для запроса комиссии"""
    amount: float
    commission_rate: float = 0.025


@dataclass
class CommissionResponseDTO:
    """DTO для ответа комиссии"""
    commission: float
    amount: float
    rate: float