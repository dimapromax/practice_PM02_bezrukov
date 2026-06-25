from datetime import datetime, timedelta


def generate_test_payment_data(booking_id: int = 1, amount: float = 100.00) -> dict:
    """Сгенерировать тестовые данные для платежа."""
    return {
        'booking_id': booking_id,
        'amount': amount,
        'payment_method': 'card',
        'currency': 'USD'
    }


def is_valid_currency(currency: str) -> bool:
    """Проверить корректность валюты."""
    allowed = ["USD", "EUR", "RUB", "JPY", "GBP", "CNY"]
    return currency in allowed


def format_amount(amount: float) -> str:
    """Форматировать сумму для отображения."""
    return f"{amount:.2f}"