import pytest
from unittest.mock import Mock, patch

from src.application.services import PaymentService
from src.application.dto import PaymentRequestDTO, PaymentResponseDTO


class TestPaymentAPI:
    """Интеграционные тесты для API"""
    
    @pytest.fixture
    def service(self):
        return PaymentService()
    
    def test_api_process_payment_success(self, service):
        """Успешная обработка платежа через API"""
        request = PaymentRequestDTO(amount=1000.0, method="card")
        response = service.process_payment(request)
        
        assert response.success is True
        assert response.transaction_id is not None
    
    def test_api_process_payment_invalid_amount(self, service):
        """Невалидная сумма через API"""
        request = PaymentRequestDTO(amount=0.0, method="card")
        with pytest.raises(Exception):
            service.process_payment(request)
    
    def test_api_process_payment_refund(self, service):
        """Возврат через API"""
        # Сначала создаем платеж
        payment_request = PaymentRequestDTO(amount=1000.0, method="card")
        payment_response = service.process_payment(payment_request)
        
        # Затем делаем возврат
        from src.application.dto import RefundRequestDTO
        refund_request = RefundRequestDTO(
            transaction_id=payment_response.transaction_id,
            original_amount=1000.0,
            days_before=7
        )
        refund_response = service.refund_payment(refund_request)
        
        assert refund_response.success is True
        assert refund_response.refund_amount == 1000.0