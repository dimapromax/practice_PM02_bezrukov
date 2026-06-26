import logging
import math
from typing import Optional

from src.core.domain import Transaction, PaymentMethod, PaymentStatus, Refund
from src.core.exceptions import (
    PaymentError,
    InvalidAmountError,
    TransactionNotFoundError,
    PaymentMethodNotSupportedError
)
from src.application.dto import (
    PaymentRequestDTO,
    PaymentResponseDTO,
    RefundRequestDTO,
    RefundResponseDTO,
    CommissionRequestDTO,
    CommissionResponseDTO
)
from src.utils.validators import validate_card_number
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PaymentService:
    """
    Сервис для обработки платежей.
    
    Основные функции:
    - Обработка платежей (process_payment)
    - Выполнение возвратов (refund_payment)
    - Расчет комиссии (calculate_commission)
    """
    
    def __init__(self):
        self._transactions: dict[str, Transaction] = {}
        self._refunds: dict[str, Refund] = {}
    
    def calculate_commission(
        self,
        amount: float,
        commission_rate: float = 0.025
    ) -> CommissionResponseDTO:
        """
        Рассчитать комиссию за платеж.
        
        Правила:
        - Комиссия = amount * commission_rate
        - Минимальная комиссия: 10 руб.
        - Максимальная комиссия: 1000 руб.
        - Округление до 2 знаков (вверх)
        """
        if amount < 0:
            raise InvalidAmountError("Сумма не может быть отрицательной")
        
        commission = amount * commission_rate
        
        # Округление вверх до 2 знаков
        commission = math.ceil(commission * 100) / 100
        
        # Применяем минимальную и максимальную комиссию
        if commission < 10:
            commission = 10.0
        elif commission > 1000:
            commission = 1000.0
        
        logger.debug(f"Commission calculated: {commission} for amount {amount}")
        
        return CommissionResponseDTO(
            commission=commission,
            amount=amount,
            rate=commission_rate
        )
    
    def process_payment(self, request: PaymentRequestDTO) -> PaymentResponseDTO:
        """
        Обработать платеж.
        """
        logger.info(f"Processing payment: {request.amount} via {request.method}")
        
        # Валидация
        if request.amount <= 0:
            raise InvalidAmountError("Сумма должна быть положительной")
        
        # Проверка метода оплаты
        try:
            method = PaymentMethod(request.method.lower())
        except ValueError:
            raise PaymentMethodNotSupportedError(
                f"Неподдерживаемый метод оплаты: {request.method}"
            )
        
        # Расчет комиссии
        if method == PaymentMethod.CASH:
            commission = 0.0
        else:
            commission_result = self.calculate_commission(request.amount)
            commission = commission_result.commission
        
        net_amount = request.amount - commission
        
        # Создание транзакции
        transaction = Transaction(
            amount=request.amount,
            method=method,
            commission=commission,
            net_amount=net_amount,
            metadata=request.metadata or {}
        )
        transaction.complete()
        
        # Сохранение транзакции
        self._transactions[transaction.id] = transaction
        
        logger.info(f"Payment completed: {transaction.id}")
        
        return PaymentResponseDTO(
            success=True,
            transaction_id=transaction.id,
            amount=transaction.amount,
            commission=transaction.commission,
            net_amount=transaction.net_amount,
            status=transaction.status.value
        )
    
    def refund_payment(self, request: RefundRequestDTO) -> RefundResponseDTO:
        """
        Выполнить возврат платежа.
        """
        logger.info(f"Processing refund for: {request.transaction_id}")
        
        # Проверка существования транзакции
        transaction = self._transactions.get(request.transaction_id)
        if not transaction:
            return RefundResponseDTO(
                success=False,
                error="Транзакция не найдена"
            )
        
        # Валидация
        if request.days_before < 0:
            raise InvalidAmountError("Количество дней до заезда не может быть отрицательным")
        
        if request.original_amount <= 0:
            raise InvalidAmountError("Сумма должна быть положительной")
        
        # Определение процента возврата
        if request.days_before >= 7:
            refund_percent = 1.0
            fee_percent = 0.0
        elif request.days_before >= 3:
            refund_percent = 0.85
            fee_percent = 0.15
        elif request.days_before >= 1:
            refund_percent = 0.50
            fee_percent = 0.50
        else:
            refund_percent = 0.0
            fee_percent = 1.0
        
        # ИСПРАВЛЕНО: сначала округляем сумму возврата, затем fee = original - refund
        # Это гарантирует, что refund_amount + fee = original_amount
        refund_amount = self._round_money(request.original_amount * refund_percent)
        fee = self._round_money(request.original_amount - refund_amount)
        
        # Создание возврата
        refund = Refund(
            transaction_id=request.transaction_id,
            original_amount=request.original_amount,
            refund_amount=refund_amount,
            fee=fee,
            days_before=request.days_before
        )
        self._refunds[refund.id] = refund
        
        # Обновление статуса транзакции
        transaction.refund()
        
        logger.info(f"Refund completed: {refund.id}")
        
        return RefundResponseDTO(
            success=True,
            refund_amount=refund_amount,
            fee=fee
        )
    
    def _round_money(self, value: float) -> float:
        """
        Округление денежной суммы до 2 знаков после запятой.
        Использует Decimal для точного округления.
        """
        from decimal import Decimal, getcontext, ROUND_HALF_UP
        getcontext().prec = 10
        decimal_value = Decimal(str(value))
        rounded = decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return float(rounded)
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Получить транзакцию по ID"""
        return self._transactions.get(transaction_id)
    
    def get_refund(self, refund_id: str) -> Optional[Refund]:
        """Получить возврат по ID"""
        return self._refunds.get(refund_id)
    
    def calculate_total_with_tax(
        self,
        amount: float,
        tax_rate: float = 0.20
    ) -> float:
        """Рассчитать сумму с налогом"""
        if amount < 0:
            return 0.0
        
        total = amount * (1 + tax_rate)
        return self._round_money(total)
    
    def validate_card_number(self, card_number: str) -> bool:
        """Проверить номер карты (алгоритм Луна)"""
        return validate_card_number(card_number)