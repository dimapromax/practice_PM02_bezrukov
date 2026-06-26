import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from src.application.services import PaymentService
from src.application.dto import (
    PaymentRequestDTO,
    RefundRequestDTO,
    CommissionRequestDTO
)
from src.core.exceptions import (
    PaymentError,
    InvalidAmountError,
    TransactionNotFoundError,
    PaymentMethodNotSupportedError
)


class TestPaymentService:
    """Тесты для PaymentService"""
    
    @pytest.fixture
    def service(self):
        """Создание сервиса для тестов"""
        return PaymentService()
    
    # ============================================================
    # Тесты для calculate_commission
    # ============================================================
    
    def test_calculate_commission_basic(self, service):
        """Базовая комиссия (2.5%)"""
        result = service.calculate_commission(1000.0)
        assert result.commission == 25.0
    
    def test_calculate_commission_minimum(self, service):
        """Минимальная комиссия (10 руб)"""
        result = service.calculate_commission(100.0)
        assert result.commission == 10.0
    
    def test_calculate_commission_maximum(self, service):
        """Максимальная комиссия (1000 руб)"""
        result = service.calculate_commission(100000.0)
        assert result.commission == 1000.0
    
    def test_calculate_commission_negative(self, service):
        """Отрицательная сумма"""
        with pytest.raises(InvalidAmountError):
            service.calculate_commission(-100.0)
    
    def test_calculate_commission_zero(self, service):
        """Нулевая сумма"""
        result = service.calculate_commission(0.0)
        assert result.commission == 10.0
    
    @pytest.mark.parametrize("amount,expected", [
        (500.0, 12.5),
        (2000.0, 50.0),
        (40000.0, 1000.0),
        (150.0, 10.0),
    ])
    def test_calculate_commission_parametrized(self, service, amount, expected):
        """Параметризованные тесты комиссии"""
        result = service.calculate_commission(amount)
        assert result.commission == expected
    
    # ============================================================
    # Тесты для process_payment
    # ============================================================
    
    def test_process_payment_card(self, service):
        """Оплата картой"""
        request = PaymentRequestDTO(amount=1000.0, method="card")
        result = service.process_payment(request)
        
        assert result.success is True
        assert result.amount == 1000.0
        assert result.commission == 25.0
        assert result.net_amount == 975.0
        assert result.transaction_id is not None
    
    def test_process_payment_cash(self, service):
        """Оплата наличными (без комиссии)"""
        request = PaymentRequestDTO(amount=1000.0, method="cash")
        result = service.process_payment(request)
        
        assert result.success is True
        assert result.commission == 0.0
        assert result.net_amount == 1000.0
    
    def test_process_payment_zero(self, service):
        """Нулевая сумма"""
        request = PaymentRequestDTO(amount=0.0, method="card")
        with pytest.raises(InvalidAmountError):
            service.process_payment(request)
    
    def test_process_payment_negative(self, service):
        """Отрицательная сумма"""
        request = PaymentRequestDTO(amount=-100.0, method="card")
        with pytest.raises(InvalidAmountError):
            service.process_payment(request)
    
    def test_process_payment_invalid_method(self, service):
        """Неподдерживаемый метод оплаты"""
        request = PaymentRequestDTO(amount=1000.0, method="bitcoin")
        with pytest.raises(PaymentMethodNotSupportedError):
            service.process_payment(request)
    
    def test_process_payment_stores_transaction(self, service):
        """Проверка сохранения транзакции"""
        request = PaymentRequestDTO(amount=1000.0, method="card")
        result = service.process_payment(request)
        
        transaction = service.get_transaction(result.transaction_id)
        assert transaction is not None
        assert transaction.amount == 1000.0
    
    # ============================================================
    # Тесты для refund_payment
    # ============================================================
    
    def test_refund_payment_full(self, service):
        """Полный возврат (7+ дней)"""
        # 1. Сначала создаем транзакцию
        payment_request = PaymentRequestDTO(amount=1000.0, method="card")
        payment_result = service.process_payment(payment_request)
        transaction_id = payment_result.transaction_id
        
        # 2. Делаем возврат
        request = RefundRequestDTO(
            transaction_id=transaction_id,
            original_amount=1000.0,
            days_before=7
        )
        result = service.refund_payment(request)
        
        assert result.success is True
        assert result.refund_amount == 1000.0
        assert result.fee == 0.0
    
    def test_refund_payment_partial_85(self, service):
        """85% возврат (3-6 дней)"""
        # 1. Сначала создаем транзакцию
        payment_request = PaymentRequestDTO(amount=1000.0, method="card")
        payment_result = service.process_payment(payment_request)
        transaction_id = payment_result.transaction_id
        
        # 2. Делаем возврат
        request = RefundRequestDTO(
            transaction_id=transaction_id,
            original_amount=1000.0,
            days_before=3
        )
        result = service.refund_payment(request)
        
        assert result.success is True
        assert result.refund_amount == 850.0
        assert result.fee == 150.0
    
    def test_refund_payment_partial_50(self, service):
        """50% возврат (1-2 дня)"""
        # 1. Сначала создаем транзакцию
        payment_request = PaymentRequestDTO(amount=1000.0, method="card")
        payment_result = service.process_payment(payment_request)
        transaction_id = payment_result.transaction_id
        
        # 2. Делаем возврат
        request = RefundRequestDTO(
            transaction_id=transaction_id,
            original_amount=1000.0,
            days_before=1
        )
        result = service.refund_payment(request)
        
        assert result.success is True
        assert result.refund_amount == 500.0
        assert result.fee == 500.0
    
    def test_refund_payment_no_refund(self, service):
        """0% возврат (день заезда)"""
        # 1. Сначала создаем транзакцию
        payment_request = PaymentRequestDTO(amount=1000.0, method="card")
        payment_result = service.process_payment(payment_request)
        transaction_id = payment_result.transaction_id
        
        # 2. Делаем возврат
        request = RefundRequestDTO(
            transaction_id=transaction_id,
            original_amount=1000.0,
            days_before=0
        )
        result = service.refund_payment(request)
        
        assert result.success is True
        assert result.refund_amount == 0.0
        assert result.fee == 1000.0
    
    def test_refund_payment_invalid_transaction(self, service):
        """Несуществующая транзакция"""
        request = RefundRequestDTO(
            transaction_id="INVALID",
            original_amount=1000.0,
            days_before=7
        )
        result = service.refund_payment(request)
        
        assert result.success is False
        assert "не найдена" in result.error
    
    def test_refund_payment_negative_days(self, service):
        """Отрицательное количество дней"""
        # 1. Сначала создаем транзакцию
        payment_request = PaymentRequestDTO(amount=1000.0, method="card")
        payment_result = service.process_payment(payment_request)
        transaction_id = payment_result.transaction_id
        
        # 2. Пытаемся сделать возврат с отрицательными днями
        request = RefundRequestDTO(
            transaction_id=transaction_id,
            original_amount=1000.0,
            days_before=-1
        )
        with pytest.raises(InvalidAmountError):
            service.refund_payment(request)
    
    def test_refund_payment_negative_amount(self, service):
        """Отрицательная сумма"""
        # 1. Сначала создаем транзакцию
        payment_request = PaymentRequestDTO(amount=1000.0, method="card")
        payment_result = service.process_payment(payment_request)
        transaction_id = payment_result.transaction_id
        
        # 2. Пытаемся сделать возврат с отрицательной суммой
        request = RefundRequestDTO(
            transaction_id=transaction_id,
            original_amount=-100.0,
            days_before=7
        )
        with pytest.raises(InvalidAmountError):
            service.refund_payment(request)
    
    # ============================================================
    # Тесты для calculate_total_with_tax
    # ============================================================
    
    def test_calculate_total_with_tax_basic(self, service):
        """Расчет с налогом (20%)"""
        result = service.calculate_total_with_tax(1000.0)
        assert result == 1200.0
    
    def test_calculate_total_with_tax_custom(self, service):
        """Расчет с пользовательским налогом"""
        result = service.calculate_total_with_tax(1000.0, 0.10)
        assert result == 1100.0
    
    def test_calculate_total_with_tax_negative(self, service):
        """Отрицательная сумма"""
        result = service.calculate_total_with_tax(-100.0)
        assert result == 0.0
    
    # ============================================================
    # Тесты для validate_card_number
    # ============================================================
    
    def test_validate_card_number_valid_visa(self, service):
        """Валидный номер карты (Visa)"""
        result = service.validate_card_number("4111111111111111")
        assert result is True
    
    def test_validate_card_number_valid_mastercard(self, service):
        """Валидный номер карты (Mastercard)"""
        result = service.validate_card_number("5555555555554444")
        assert result is True
    
    def test_validate_card_number_invalid(self, service):
        """Невалидный номер карты"""
        result = service.validate_card_number("4111111111111112")
        assert result is False
    
    def test_validate_card_number_with_spaces(self, service):
        """Номер карты с пробелами"""
        result = service.validate_card_number("4111 1111 1111 1111")
        assert result is True
    
    def test_validate_card_number_short(self, service):
        """Слишком короткий номер"""
        result = service.validate_card_number("123")
        assert result is False
    
    def test_validate_card_number_empty(self, service):
        """Пустая строка"""
        result = service.validate_card_number("")
        assert result is False
    
    def test_validate_card_number_with_letters(self, service):
        """Номер с буквами"""
        result = service.validate_card_number("4111ABCD11111111")
        assert result is False
    
    # ============================================================
    # Дополнительные тесты для покрытия
    # ============================================================
    
    def test_calculate_refund_amount_with_fraction(self, service):
        """Возврат с дробной суммой"""
        # 1. Сначала создаем транзакцию
        payment_request = PaymentRequestDTO(amount=100.50, method="card")
        payment_result = service.process_payment(payment_request)
        transaction_id = payment_result.transaction_id
        
        # 2. Делаем возврат
        request = RefundRequestDTO(
            transaction_id=transaction_id,
            original_amount=100.50,
            days_before=3
        )
        result = service.refund_payment(request)
        assert result.success is True
        # 100.50 * 0.85 = 85.425 → 85.43
        # 100.50 - 85.43 = 15.07 (штраф)
        assert result.refund_amount == 85.43
        assert result.fee == 15.07
        # Проверка, что сумма возврата + штраф = исходная сумма
        assert result.refund_amount + result.fee == 100.50
    
    def test_process_payment_with_fraction(self, service):
        """Платеж с дробной суммой"""
        request = PaymentRequestDTO(amount=100.50, method="card")
        result = service.process_payment(request)
        # 100.50 * 0.025 = 2.5125 → 10.0 (минимум)
        assert result.commission == 10.0
        assert result.net_amount == 90.50
    
    def test_get_transaction_not_found(self, service):
        """Получение несуществующей транзакции"""
        result = service.get_transaction("INVALID")
        assert result is None
    
    def test_refund_payment_fee_calculation(self, service):
        """Проверка расчета штрафа"""
        # 1. Сначала создаем транзакцию
        payment_request = PaymentRequestDTO(amount=1000.0, method="card")
        payment_result = service.process_payment(payment_request)
        transaction_id = payment_result.transaction_id
        
        # 2. Тестируем разные варианты
        test_cases = [
            (7, 1000.0, 0.0),    # 7+ дней: 100% возврат, 0% штраф
            (3, 850.0, 150.0),   # 3-6 дней: 85% возврат, 15% штраф
            (1, 500.0, 500.0),   # 1-2 дня: 50% возврат, 50% штраф
            (0, 0.0, 1000.0),    # 0 дней: 0% возврат, 100% штраф
        ]
        
        for days, expected_refund, expected_fee in test_cases:
            request = RefundRequestDTO(
                transaction_id=transaction_id,
                original_amount=1000.0,
                days_before=days
            )
            result = service.refund_payment(request)
            assert result.success is True
            assert result.refund_amount == expected_refund
            assert result.fee == expected_fee
    
    def test_refund_payment_updates_transaction_status(self, service):
        """Проверка, что статус транзакции обновляется при возврате"""
        # 1. Сначала создаем транзакцию
        payment_request = PaymentRequestDTO(amount=1000.0, method="card")
        payment_result = service.process_payment(payment_request)
        transaction_id = payment_result.transaction_id
        
        # 2. Делаем возврат
        request = RefundRequestDTO(
            transaction_id=transaction_id,
            original_amount=1000.0,
            days_before=7
        )
        service.refund_payment(request)
        
        # 3. Проверяем статус транзакции
        transaction = service.get_transaction(transaction_id)
        assert transaction is not None
        assert transaction.status.value == "refunded"