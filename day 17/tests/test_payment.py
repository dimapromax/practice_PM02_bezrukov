import pytest
from datetime import datetime, timedelta
from src.payment import (
    create_payment,
    get_payment,
    process_payment,
    refund_payment,
    get_payments_by_booking,
    calculate_total_paid,
    validate_payment_amount,
    apply_discount_to_payment,
    clear_db
)


@pytest.fixture
def clean_db():
    """Очистить базу данных перед каждым тестом."""
    clear_db()
    yield
    clear_db()


@pytest.fixture
def sample_payment(clean_db):
    """Создать тестовый платеж."""
    payment = create_payment(
        booking_id=1,
        amount=1000.00,
        payment_method="card",
        currency="USD"
    )
    return payment


# === ТЕСТЫ ДЛЯ create_payment ===

def test_create_payment_success(clean_db):
    """Тест успешного создания платежа."""
    payment = create_payment(
        booking_id=1,
        amount=1000.00,
        payment_method="card",
        currency="USD"
    )
    
    assert payment['id'] == 1
    assert payment['booking_id'] == 1
    assert payment['amount'] == 1000.00
    assert payment['payment_method'] == "card"
    assert payment['currency'] == "USD"
    assert payment['status'] == "pending"
    assert 'created_at' in payment
    assert 'updated_at' in payment


def test_create_payment_negative_amount(clean_db):
    """Тест создания платежа с отрицательной суммой."""
    with pytest.raises(ValueError, match="Amount must be positive"):
        create_payment(1, -100.00)


def test_create_payment_zero_amount(clean_db):
    """Тест создания платежа с нулевой суммой."""
    with pytest.raises(ValueError, match="Amount must be positive"):
        create_payment(1, 0.00)


def test_create_payment_different_methods(clean_db):
    """Тест создания платежа разными методами."""
    methods = ["card", "paypal", "apple_pay", "google_pay", "bank_transfer"]
    for method in methods:
        payment = create_payment(1, 100.00, method)
        assert payment['payment_method'] == method


def test_create_payment_auto_increment(clean_db):
    """Тест автоматического увеличения ID."""
    payment1 = create_payment(1, 100.00)
    payment2 = create_payment(1, 200.00)
    payment3 = create_payment(1, 300.00)
    
    assert payment1['id'] == 1
    assert payment2['id'] == 2
    assert payment3['id'] == 3


def test_create_payment_invalid_currency(clean_db):
    """Тест создания платежа с неподдерживаемой валютой."""
    with pytest.raises(ValueError, match="Currency XXX is not supported"):
        create_payment(1, 100.00, currency="XXX")


def test_create_payment_different_currencies(clean_db):
    """Тест создания платежа с разными валютами."""
    currencies = ["USD", "EUR", "RUB", "JPY", "GBP", "CNY"]
    for currency in currencies:
        payment = create_payment(1, 100.00, currency=currency)
        assert payment['currency'] == currency


# === ТЕСТЫ ДЛЯ get_payment ===

def test_get_payment_exists(sample_payment):
    """Тест получения существующего платежа."""
    payment = get_payment(sample_payment['id'])
    assert payment is not None
    assert payment['id'] == sample_payment['id']


def test_get_payment_not_exists(clean_db):
    """Тест получения несуществующего платежа."""
    payment = get_payment(999)
    assert payment is None


# === ТЕСТЫ ДЛЯ process_payment ===

def test_process_payment_success(sample_payment):
    """Тест успешной обработки платежа."""
    result = process_payment(sample_payment['id'])
    
    assert result['status'] == "completed"
    assert 'commission' in result
    assert result['commission'] == 29.00
    assert result['updated_at'] != sample_payment['created_at']


def test_process_payment_not_found(clean_db):
    """Тест обработки несуществующего платежа."""
    with pytest.raises(ValueError, match="Payment not found"):
        process_payment(999)


def test_process_payment_already_completed(sample_payment):
    """Тест обработки уже обработанного платежа."""
    process_payment(sample_payment['id'])
    
    with pytest.raises(ValueError, match="Payment already processed"):
        process_payment(sample_payment['id'])


def test_process_payment_commission_rounding(clean_db):
    """Тест правильного округления комиссии."""
    test_cases = [
        (100.00, 2.90),
        (1000.00, 29.00),
        (99.99, 2.90),
        (0.01, 0.00),
        (999.99, 29.00),
    ]
    
    for amount, expected_commission in test_cases:
        payment = create_payment(1, amount)
        result = process_payment(payment['id'])
        assert result['commission'] == expected_commission


def test_process_payment_multiple(clean_db):
    """Тест обработки нескольких платежей."""
    payment1 = create_payment(1, 100.00)
    payment2 = create_payment(1, 200.00)
    
    process_payment(payment1['id'])
    process_payment(payment2['id'])
    
    assert get_payment(payment1['id'])['status'] == "completed"
    assert get_payment(payment2['id'])['status'] == "completed"


# === ТЕСТЫ ДЛЯ refund_payment ===

def test_refund_payment_success(sample_payment):
    """Тест успешного возврата платежа."""
    process_payment(sample_payment['id'])
    
    result = refund_payment(sample_payment['id'], "Customer request")
    
    assert result['status'] == "refunded"
    assert result['refund_amount'] == sample_payment['amount']
    assert result['refund_reason'] == "Customer request"
    assert 'updated_at' in result


def test_refund_payment_not_found(clean_db):
    """Тест возврата несуществующего платежа."""
    with pytest.raises(ValueError, match="Payment not found"):
        refund_payment(999)


def test_refund_payment_not_completed(sample_payment):
    """Тест возврата необработанного платежа."""
    with pytest.raises(ValueError, match="Payment not completed"):
        refund_payment(sample_payment['id'])


def test_refund_payment_full_amount(clean_db):
    """Тест возврата полной суммы."""
    payment = create_payment(1, 1000.00)
    process_payment(payment['id'])
    
    result = refund_payment(payment['id'])
    assert result['refund_amount'] == 1000.00


def test_refund_payment_multiple(clean_db):
    """Тест возврата нескольких платежей."""
    payment1 = create_payment(1, 100.00)
    payment2 = create_payment(1, 200.00)
    
    process_payment(payment1['id'])
    process_payment(payment2['id'])
    
    refund_payment(payment1['id'])
    refund_payment(payment2['id'])
    
    assert get_payment(payment1['id'])['status'] == "refunded"
    assert get_payment(payment2['id'])['status'] == "refunded"


# === ТЕСТЫ ДЛЯ get_payments_by_booking ===

def test_get_payments_by_booking(clean_db):
    """Тест получения платежей по бронированию."""
    create_payment(1, 100.00)
    create_payment(1, 200.00)
    create_payment(2, 300.00)
    
    payments_booking1 = get_payments_by_booking(1)
    assert len(payments_booking1) == 2
    assert all(p['booking_id'] == 1 for p in payments_booking1)
    
    payments_booking2 = get_payments_by_booking(2)
    assert len(payments_booking2) == 1
    assert payments_booking2[0]['booking_id'] == 2
    
    payments_booking3 = get_payments_by_booking(3)
    assert len(payments_booking3) == 0


# === ТЕСТЫ ДЛЯ calculate_total_paid ===

def test_calculate_total_paid_basic(clean_db):
    """Тест расчета общей суммы оплаченных платежей."""
    payment1 = create_payment(1, 100.00)
    payment2 = create_payment(1, 200.00)
    payment3 = create_payment(1, 300.00)
    
    process_payment(payment1['id'])
    process_payment(payment2['id'])
    process_payment(payment3['id'])
    
    total = calculate_total_paid(1)
    assert total == 600.00


def test_calculate_total_paid_with_refunds(clean_db):
    """Тест расчета суммы с учетом возвратов."""
    payment1 = create_payment(1, 100.00)
    payment2 = create_payment(1, 200.00)
    
    process_payment(payment1['id'])
    process_payment(payment2['id'])
    refund_payment(payment1['id'])
    
    total = calculate_total_paid(1)
    assert total == 200.00


def test_calculate_total_paid_with_pending(clean_db):
    """Тест расчета суммы с учетом ожидающих платежей."""
    payment1 = create_payment(1, 100.00)
    payment2 = create_payment(1, 200.00)
    
    process_payment(payment1['id'])
    # payment2 остается в статусе pending
    
    total = calculate_total_paid(1)
    assert total == 100.00


def test_calculate_total_paid_no_payments(clean_db):
    """Тест расчета суммы при отсутствии платежей."""
    total = calculate_total_paid(1)
    assert total == 0.0


def test_calculate_total_paid_large_numbers(clean_db):
    """Тест расчета с большими числами."""
    payment1 = create_payment(1, 999999.99)
    payment2 = create_payment(1, 888888.88)
    
    process_payment(payment1['id'])
    process_payment(payment2['id'])
    
    total = calculate_total_paid(1)
    assert total == 1888888.87


# === ТЕСТЫ ДЛЯ validate_payment_amount ===

def test_validate_payment_amount_positive(clean_db):
    """Тест валидации положительной суммы."""
    assert validate_payment_amount(100.00) is True
    assert validate_payment_amount(0.01) is True


def test_validate_payment_amount_negative(clean_db):
    """Тест валидации отрицательной суммы."""
    assert validate_payment_amount(-100.00) is False
    assert validate_payment_amount(0.00) is False


def test_validate_payment_amount_usd_limit(clean_db):
    """Тест лимита для USD."""
    assert validate_payment_amount(10000.00, "USD") is True
    assert validate_payment_amount(10000.01, "USD") is False


def test_validate_payment_amount_other_currencies(clean_db):
    """Тест валидации для других валют."""
    # EUR: лимит 9000.00
    assert validate_payment_amount(9000.00, "EUR") is True
    assert validate_payment_amount(9000.01, "EUR") is False
    
    # RUB: лимит 1000000.00
    assert validate_payment_amount(1000000.00, "RUB") is True
    assert validate_payment_amount(1000000.01, "RUB") is False
    
    # JPY: лимит 1000000.00
    assert validate_payment_amount(1000000.00, "JPY") is True
    assert validate_payment_amount(1000000.01, "JPY") is False
    
    # GBP: лимит 8000.00
    assert validate_payment_amount(8000.00, "GBP") is True
    assert validate_payment_amount(8000.01, "GBP") is False
    
    # CNY: лимит 70000.00
    assert validate_payment_amount(70000.00, "CNY") is True
    assert validate_payment_amount(70000.01, "CNY") is False


def test_validate_payment_amount_edge_cases(clean_db):
    """Тест граничных случаев."""
    assert validate_payment_amount(9999.99, "USD") is True
    assert validate_payment_amount(10000.00, "USD") is True
    assert validate_payment_amount(10000.01, "USD") is False
    assert validate_payment_amount(0.01, "USD") is True


def test_validate_payment_amount_unknown_currency(clean_db):
    """Тест валидации с неизвестной валютой."""
    assert validate_payment_amount(100000.00, "XXX") is True


# === ТЕСТЫ ДЛЯ apply_discount_to_payment ===

def test_apply_discount_success(sample_payment):
    """Тест успешного применения скидки."""
    result = apply_discount_to_payment(sample_payment['id'], 10.0)
    
    assert result['discount_amount'] == 100.00
    assert result['amount'] == 900.00


def test_apply_discount_zero_percent(sample_payment):
    """Тест скидки 0%."""
    result = apply_discount_to_payment(sample_payment['id'], 0.0)
    
    assert result['discount_amount'] == 0.0
    assert result['amount'] == 1000.00


def test_apply_discount_hundred_percent(sample_payment):
    """Тест скидки 100%."""
    result = apply_discount_to_payment(sample_payment['id'], 100.0)
    
    assert result['discount_amount'] == 1000.00
    assert result['amount'] == 0.00


def test_apply_discount_invalid_percent(sample_payment):
    """Тест недопустимого процента скидки."""
    with pytest.raises(ValueError, match="Discount must be between 0 and 100"):
        apply_discount_to_payment(sample_payment['id'], -10.0)
    
    with pytest.raises(ValueError, match="Discount must be between 0 and 100"):
        apply_discount_to_payment(sample_payment['id'], 150.0)


def test_apply_discount_not_found(clean_db):
    """Тест применения скидки к несуществующему платежу."""
    with pytest.raises(ValueError, match="Payment not found"):
        apply_discount_to_payment(999, 10.0)


def test_apply_discount_rounding(clean_db):
    """Тест округления при применении скидки."""
    payment = create_payment(1, 99.99)
    result = apply_discount_to_payment(payment['id'], 33.33)
    
    expected_discount = round(99.99 * 0.3333, 2)
    expected_amount = round(99.99 - expected_discount, 2)
    
    assert result['discount_amount'] == expected_discount
    assert result['amount'] == expected_amount


def test_apply_discount_multiple(clean_db):
    """Тест применения скидки к нескольким платежам."""
    payment1 = create_payment(1, 100.00)
    payment2 = create_payment(1, 200.00)
    payment3 = create_payment(1, 300.00)
    
    apply_discount_to_payment(payment1['id'], 10.0)
    apply_discount_to_payment(payment2['id'], 20.0)
    apply_discount_to_payment(payment3['id'], 30.0)
    
    assert get_payment(payment1['id'])['amount'] == 90.00
    assert get_payment(payment2['id'])['amount'] == 160.00
    assert get_payment(payment3['id'])['amount'] == 210.00


def test_apply_discount_updates_timestamp(clean_db):
    """Тест обновления времени при применении скидки."""
    payment = create_payment(1, 100.00)
    created_at = payment['created_at']
    
    apply_discount_to_payment(payment['id'], 10.0)
    updated_payment = get_payment(payment['id'])
    
    assert updated_payment['updated_at'] != created_at


# === ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ ДЛЯ ПОКРЫТИЯ ===

def test_large_amount_payment(clean_db):
    """Тест создания платежа с большой суммой."""
    large_amount = 99999999.99
    payment = create_payment(1, large_amount)
    assert payment['amount'] == large_amount


def test_small_amount_payment(clean_db):
    """Тест создания платежа с минимальной суммой."""
    payment = create_payment(1, 0.01)
    assert payment['amount'] == 0.01


def test_payment_processing_time(clean_db):
    """Тест времени обработки платежа."""
    payment = create_payment(1, 100.00)
    created_at = payment['created_at']
    
    process_payment(payment['id'])
    updated_payment = get_payment(payment['id'])
    
    assert updated_payment['updated_at'] != created_at
    assert datetime.fromisoformat(updated_payment['updated_at']) > \
           datetime.fromisoformat(created_at)


def test_payment_currency_validation(clean_db):
    """Тест валидации валют."""
    payment = create_payment(1, 100.00, currency="USD")
    assert payment['currency'] == "USD"
    
    payment = create_payment(1, 100.00, currency="EUR")
    assert payment['currency'] == "EUR"


def test_clear_db(clean_db):
    """Тест очистки базы данных."""
    create_payment(1, 100.00)
    create_payment(1, 200.00)
    
    assert len(get_payments_by_booking(1)) == 2
    
    clear_db()
    assert len(get_payments_by_booking(1)) == 0


def test_payment_status_flow(clean_db):
    """Тест полного жизненного цикла платежа."""
    # Создание
    payment = create_payment(1, 100.00)
    assert payment['status'] == 'pending'
    
    # Обработка
    process_payment(payment['id'])
    assert get_payment(payment['id'])['status'] == 'completed'
    
    # Возврат
    refund_payment(payment['id'])
    assert get_payment(payment['id'])['status'] == 'refunded'