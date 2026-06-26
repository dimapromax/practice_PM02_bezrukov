import pytest

from src.utils.validators import (
    validate_card_number,
    validate_amount,
    validate_email,
    validate_phone
)


class TestValidators:
    """Тесты для валидаторов"""
    
    def test_validate_card_number_valid(self):
        assert validate_card_number("4111111111111111") is True
    
    def test_validate_card_number_invalid(self):
        assert validate_card_number("4111111111111112") is False
    
    def test_validate_card_number_with_spaces(self):
        assert validate_card_number("4111 1111 1111 1111") is True
    
    def test_validate_card_number_short(self):
        assert validate_card_number("123") is False
    
    def test_validate_card_number_empty(self):
        assert validate_card_number("") is False
    
    def test_validate_amount_positive(self):
        assert validate_amount(100.0) is True
    
    def test_validate_amount_zero(self):
        assert validate_amount(0.0) is False
    
    def test_validate_amount_negative(self):
        assert validate_amount(-100.0) is False
    
    def test_validate_email_valid(self):
        assert validate_email("test@example.com") is True
    
    def test_validate_email_invalid(self):
        assert validate_email("invalid-email") is False
    
    def test_validate_phone_valid(self):
        assert validate_phone("+79991234567") is True
    
    def test_validate_phone_with_spaces(self):
        assert validate_phone("+7 999 123 45 67") is True
    
    def test_validate_phone_short(self):
        assert validate_phone("123") is False