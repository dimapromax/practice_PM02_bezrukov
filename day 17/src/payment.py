from typing import Optional, Dict, Any, List
from datetime import datetime

# База данных платежей в памяти
_payments_db: List[Dict[str, Any]] = []
_payment_counter = 1


def create_payment(
    booking_id: int,
    amount: float,
    payment_method: str = "card",
    currency: str = "USD"
) -> Dict[str, Any]:
   
    global _payment_counter
    
    # Проверка суммы
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    # Проверка валюты
    allowed_currencies = ["USD", "EUR", "RUB", "JPY", "GBP", "CNY"]
    if currency not in allowed_currencies:
        raise ValueError(f"Currency {currency} is not supported")
    
    payment = {
        'id': _payment_counter,
        'booking_id': booking_id,
        'amount': amount,
        'payment_method': payment_method,
        'currency': currency,
        'status': 'pending',  # pending, completed, failed, refunded
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'commission': 0.0,
        'discount_amount': 0.0,
        'refund_amount': 0.0,
        'refund_reason': ""
    }
    
    _payments_db.append(payment)
    _payment_counter += 1
    return payment


def process_payment(payment_id: int) -> Dict[str, Any]:
   
    payment = get_payment(payment_id)
    if not payment:
        raise ValueError("Payment not found")
    
    # Проверка статуса
    if payment['status'] != 'pending':
        raise ValueError("Payment already processed")
    
    # Правильное округление комиссии
    commission = round(payment['amount'] * 0.029, 2)
    payment['commission'] = commission
    
    payment['status'] = 'completed'
    payment['updated_at'] = datetime.now().isoformat()
    
    return payment


def refund_payment(payment_id: int, reason: str = "") -> Dict[str, Any]:
   
    payment = get_payment(payment_id)
    if not payment:
        raise ValueError("Payment not found")
    
    # Проверка, что платеж обработан
    if payment['status'] != 'completed':
        raise ValueError("Payment not completed")
    
    # Возврат полной суммы
    payment['status'] = 'refunded'
    payment['refund_amount'] = payment['amount']
    payment['refund_reason'] = reason
    payment['updated_at'] = datetime.now().isoformat()
    
    return payment


def get_payment(payment_id: int) -> Optional[Dict[str, Any]]:
    """Получить платеж по ID."""
    for payment in _payments_db:
        if payment['id'] == payment_id:
            return payment
    return None


def get_payments_by_booking(booking_id: int) -> List[Dict[str, Any]]:
    """Получить все платежи для бронирования."""
    return [p for p in _payments_db if p['booking_id'] == booking_id]


def calculate_total_paid(booking_id: int) -> float:
    
    payments = get_payments_by_booking(booking_id)
    total = 0.0
    for payment in payments:
        # Учитываем только completed и не refunded
        if payment['status'] == 'completed':
            total += payment['amount']
    return total


def validate_payment_amount(amount: float, currency: str = "USD") -> bool:
    
    if amount <= 0:
        return False
    
    # Разные лимиты для разных валют
    limits = {
        "USD": 10000.00,
        "EUR": 9000.00,
        "RUB": 1000000.00,
        "JPY": 1000000.00,
        "GBP": 8000.00,
        "CNY": 70000.00,
    }
    
    limit = limits.get(currency, float('inf'))
    return amount <= limit


def apply_discount_to_payment(
    payment_id: int,
    discount_percent: float
) -> Dict[str, Any]:
   
    payment = get_payment(payment_id)
    if not payment:
        raise ValueError("Payment not found")
    
    # Проверка процента скидки
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    
    # Округление до 2 знаков
    discount_amount = round(payment['amount'] * (discount_percent / 100), 2)
    payment['discount_amount'] = discount_amount
    payment['amount'] = round(payment['amount'] - discount_amount, 2)
    payment['updated_at'] = datetime.now().isoformat()
    
    return payment


def clear_db():
    """Очистить базу данных (для тестов)."""
    global _payments_db, _payment_counter
    _payments_db = []
    _payment_counter = 1