

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import random

from fake_validator import FakeValidator, create_validator


# ============================================================
# Фикстуры
# ============================================================

@pytest.fixture
def validator() -> FakeValidator:
    """Создание валидатора для тестов"""
    return create_validator(chaos_mode=False)


@pytest.fixture
def chaos_validator() -> FakeValidator:
    """Валидатор с режимом хаоса для проверки устойчивости"""
    return create_validator(chaos_mode=True, chaos_probability=0.1)


@pytest.fixture
def base_order() -> Dict[str, Any]:
    """Базовый корректный заказ"""
    now = datetime.now()
    return {
        "order_id": "ORD-TEST-001",
        "user_id": "USR-TEST-001",
        "items": [
            {"product_id": "P001", "quantity": 2, "price": 500, "category": "Food"}
        ],
        "total_amount": 1000,
        "created_at": now.isoformat(),
        "user_created_at": (now - timedelta(days=30)).isoformat(),
        "user_email": "test@example.com",
        "email_last_changed": (now - timedelta(hours=2)).isoformat(),
        "delivery_country": "RU",
        "wallet_country": "RU",
        "age_verified": False,
        "order_time": "10:00:00"
    }


# ============================================================
# Вспомогательные функции
# ============================================================

def create_order(**kwargs) -> Dict[str, Any]:
    """Создание заказа с переопределёнными полями"""
    now = datetime.now()
    defaults = {
        "order_id": "ORD-TEST",
        "user_id": "USR-TEST",
        "items": [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Food"}],
        "total_amount": 100,
        "created_at": now.isoformat(),
        "user_created_at": (now - timedelta(days=30)).isoformat(),
        "user_email": "test@example.com",
        "email_last_changed": (now - timedelta(hours=2)).isoformat(),
        "delivery_country": "RU",
        "wallet_country": "RU",
        "age_verified": False,
        "order_time": "10:00:00"
    }
    defaults.update(kwargs)
    return defaults


def has_reason(result: Dict[str, Any], reason: str) -> bool:
    """Проверка наличия причины в результате"""
    return any(reason in r for r in result.get("reasons", []))


# ============================================================
# 2.2 Параметризованные тесты (Decision Table)
# ============================================================

@pytest.mark.parametrize("order_kwargs,expected_valid,expected_risk_score,expected_reasons", [
    # ============================================================
    # TC-001: Валидный заказ (обычный пользователь)
    # ============================================================
    (
        {"total_amount": 1000, "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()},
        True, 0.1, []
    ),
    
    # ============================================================
    # TC-002: Сумма = 0 (граничное значение) - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {"total_amount": 0, "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()},
        False, 0.0, ["Total amount must be between 0 and 1,000,000"]
    ),
    
    # ============================================================
    # TC-003: Сумма = 1_000_000 (граничное значение) - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {"total_amount": 1000000, "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()},
        False, 0.0, ["Total amount must be between 0 and 1,000,000"]
    ),
    
    # ============================================================
    # TC-004: Сумма = 999_999.99 (граничное значение) - ВАЛИДНЫЙ
    # ============================================================
    (
        {"total_amount": 999999.99, "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()},
        True, 0.1, []
    ),
    
    # ============================================================
    # TC-005: Сумма = 0.01 (граничное значение) - ВАЛИДНЫЙ
    # ============================================================
    (
        {"total_amount": 0.01, "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()},
        True, 0.1, []
    ),
    
    # ============================================================
    # TC-006: Новый пользователь, сумма = 15_000 (граничное значение) - ВАЛИДНЫЙ
    # ============================================================
    (
        {"total_amount": 15000, "user_created_at": (datetime.now() - timedelta(days=6)).isoformat()},
        True, 0.1, []
    ),
    
    # ============================================================
    # TC-007: Новый пользователь, сумма = 15_001 (граничное значение) - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {"total_amount": 15001, "user_created_at": (datetime.now() - timedelta(days=6)).isoformat()},
        False, 0.0, ["New users (registered < 7 days) cannot order more than 15,000"]
    ),
    
    # ============================================================
    # TC-008: Количество позиций = 50 (граничное значение) - ВАЛИДНЫЙ
    # ============================================================
    (
        {
            "items": [{"product_id": f"P{i:03d}", "quantity": 1, "price": 10, "category": "Food"} for i in range(50)],
            "total_amount": 500,
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        True, 0.1, []
    ),
    
    # ============================================================
    # TC-009: Количество позиций = 51 (граничное значение) - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {
            "items": [{"product_id": f"P{i:03d}", "quantity": 1, "price": 10, "category": "Food"} for i in range(51)],
            "total_amount": 510,
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        False, 0.0, ["Order has too many items (max 50)"]
    ),
    
    # ============================================================
    # TC-010: Алкоголь, возраст подтверждён, время 08:00 - ВАЛИДНЫЙ
    # ============================================================
    (
        {
            "items": [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Alcohol"}],
            "total_amount": 100,
            "age_verified": True,
            "order_time": "08:00:00",
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        True, 0.1, []
    ),
    
    # ============================================================
    # TC-011: Алкоголь, возраст подтверждён, время 07:59 - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {
            "items": [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Alcohol"}],
            "total_amount": 100,
            "age_verified": True,
            "order_time": "07:59:59",
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        False, 0.0, ["Alcohol can only be ordered between 08:00 and 23:00"]
    ),
    
    # ============================================================
    # TC-012: Алкоголь, возраст подтверждён, время 23:00 - ВАЛИДНЫЙ
    # ============================================================
    (
        {
            "items": [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Alcohol"}],
            "total_amount": 100,
            "age_verified": True,
            "order_time": "23:00:00",
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        True, 0.1, []
    ),
    
    # ============================================================
    # TC-013: Алкоголь, возраст подтверждён, время 23:01 - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {
            "items": [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Alcohol"}],
            "total_amount": 100,
            "age_verified": True,
            "order_time": "23:01:00",
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        False, 0.0, ["Alcohol can only be ordered between 08:00 and 23:00"]
    ),
    
    # ============================================================
    # TC-014: Алкоголь, возраст НЕ подтверждён - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {
            "items": [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Alcohol"}],
            "total_amount": 100,
            "age_verified": False,
            "order_time": "10:00:00",
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        False, 0.0, ["Alcohol requires age verification"]
    ),
    
    # ============================================================
    # TC-015: Высокий риск (сумма > 100_000) - ВАЛИДНЫЙ, риск 0.9
    # ============================================================
    (
        {
            "total_amount": 100001,
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        True, 0.9, []
    ),
    
    # ============================================================
    # TC-016: Email изменён за последний час - ВАЛИДНЫЙ, риск 0.3
    # ИСПОЛЬЗУЕМ pytest.approx для сравнения с float
    # ============================================================
    (
        {
            "total_amount": 1000,
            "email_last_changed": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        True, 0.3, []
    ),
    
    # ============================================================
    # TC-017: Страны доставки и кошелька разные - ВАЛИДНЫЙ, риск 0.4
    # ============================================================
    (
        {
            "total_amount": 1000,
            "delivery_country": "US",
            "wallet_country": "RU",
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        True, 0.4, []
    ),
    
    # ============================================================
    # TC-018: Все факторы риска одновременно - ВАЛИДНЫЙ, риск 1.0 (кап)
    # ============================================================
    (
        {
            "total_amount": 100001,
            "email_last_changed": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "delivery_country": "US",
            "wallet_country": "RU",
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        True, 1.0, []
    ),
    
    # ============================================================
    # TC-019: Пустой список товаров - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {
            "items": [],
            "total_amount": 0,
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        False, 0.0, ["Order must have at least one item"]
    ),
    
    # ============================================================
    # TC-020: Отрицательная сумма - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {
            "total_amount": -100,
            "user_created_at": (datetime.now() - timedelta(days=30)).isoformat()
        },
        False, 0.0, ["Total amount must be >= 0"]
    ),
    
    # ============================================================
    # TC-021: Новый пользователь + Алкоголь (валидный)
    # ============================================================
    (
        {
            "total_amount": 10000,
            "items": [{"product_id": "P001", "quantity": 1, "price": 10000, "category": "Alcohol"}],
            "age_verified": True,
            "order_time": "14:00:00",
            "user_created_at": (datetime.now() - timedelta(days=6)).isoformat()
        },
        True, 0.1, []
    ),
    
    # ============================================================
    # TC-022: Новый пользователь + Алкоголь + Превышение суммы - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {
            "total_amount": 20000,
            "items": [{"product_id": "P001", "quantity": 1, "price": 20000, "category": "Alcohol"}],
            "age_verified": True,
            "order_time": "14:00:00",
            "user_created_at": (datetime.now() - timedelta(days=6)).isoformat()
        },
        False, 0.0, ["New users (registered < 7 days) cannot order more than 15,000"]
    ),
    
    # ============================================================
    # TC-023: Новый пользователь + Алкоголь + Ночное время - НЕВАЛИДНЫЙ
    # ============================================================
    (
        {
            "total_amount": 10000,
            "items": [{"product_id": "P001", "quantity": 1, "price": 10000, "category": "Alcohol"}],
            "age_verified": True,
            "order_time": "01:00:00",
            "user_created_at": (datetime.now() - timedelta(days=6)).isoformat()
        },
        False, 0.0, ["Alcohol can only be ordered between 08:00 and 23:00"]
    ),
    
    # ============================================================
    # TC-024: Новый пользователь, ровно 7 дней - ВАЛИДНЫЙ
    # ============================================================
    (
        {
            "total_amount": 15000,
            "user_created_at": (datetime.now() - timedelta(days=7)).isoformat()
        },
        True, 0.1, []
    ),
    
    # ============================================================
    # TC-025: Сумма = 15_001, пользователь ровно 7 дней - ВАЛИДНЫЙ
    # ============================================================
    (
        {
            "total_amount": 15001,
            "user_created_at": (datetime.now() - timedelta(days=7)).isoformat()
        },
        True, 0.1, []
    ),
])
def test_validate_order_decision_table(validator, order_kwargs, expected_valid, expected_risk_score, expected_reasons):
    """
    Тестирование Decision Table
    """
    order = create_order(**order_kwargs)
    result = validator.validate_order(order)
    
    # Проверка валидности
    assert result["valid"] == expected_valid, \
        f"Expected valid={expected_valid}, got {result['valid']}. Reasons: {result['reasons']}"
    
    # Проверка риск-скора (с использованием approx для float)
    assert result["risk_score"] == pytest.approx(expected_risk_score, rel=1e-9, abs=1e-9), \
        f"Expected risk_score ~ {expected_risk_score}, got {result['risk_score']}"
    
    # Проверка причин
    for reason in expected_reasons:
        assert has_reason(result, reason), \
            f"Expected reason '{reason}' not found in {result['reasons']}"


# ============================================================
# Дополнительный тест для проверки risk_score с float
# ============================================================

def test_risk_score_float_precision(validator):
    """Проверка, что risk_score корректно работает с float"""
    now = datetime.now()
    
    order = create_order(
        total_amount=1000,
        email_last_changed=(now - timedelta(minutes=30)).isoformat(),
        user_created_at=(now - timedelta(days=30)).isoformat()
    )
    
    result = validator.validate_order(order)
    
    # Ожидаемый риск: базовый 0.1 + 0.2 за смену email = 0.3
    # Используем approx для сравнения float
    assert result["risk_score"] == pytest.approx(0.3, rel=1e-9)
    assert result["valid"] is True


# ============================================================
# 2.3 Property-Based тесты (Hypothesis)
# ============================================================

try:
    from hypothesis import given, strategies as st, assume
    from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
    
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False
    print("Hypothesis not installed. Skipping property-based tests.")


if HAS_HYPOTHESIS:
    
    # Стратегии для генерации заказов
    @st.composite
    def valid_order_strategy(draw):
        """Генерация валидного заказа"""
        now = datetime.now()
        user_old = draw(st.booleans())
        
        items_count = draw(st.integers(min_value=1, max_value=10))
        items = []
        for i in range(items_count):
            category = draw(st.sampled_from(["Food", "Electronics", "Books", "Clothing"]))
            items.append({
                "product_id": f"P{i:03d}",
                "quantity": draw(st.integers(min_value=1, max_value=5)),
                "price": draw(st.floats(min_value=1, max_value=1000)),
                "category": category
            })
        
        total = sum(item["quantity"] * item["price"] for item in items)
        
        if user_old:
            user_created = now - timedelta(days=draw(st.integers(min_value=7, max_value=365)))
        else:
            user_created = now - timedelta(days=draw(st.integers(min_value=0, max_value=6)))
            total = min(total, 15000)
        
        return {
            "order_id": f"ORD-{draw(st.text(min_size=3, max_size=10))}",
            "user_id": f"USR-{draw(st.text(min_size=3, max_size=10))}",
            "items": items,
            "total_amount": total,
            "created_at": now.isoformat(),
            "user_created_at": user_created.isoformat(),
            "user_email": draw(st.emails()),
            "email_last_changed": (now - timedelta(hours=draw(st.integers(min_value=1, max_value=24)))).isoformat(),
            "delivery_country": draw(st.sampled_from(["RU", "US", "UK", "DE", "FR"])),
            "wallet_country": draw(st.sampled_from(["RU", "US", "UK", "DE", "FR"])),
            "age_verified": False,
            "order_time": f"{draw(st.integers(min_value=8, max_value=22))}:{draw(st.integers(min_value=0, max_value=59)):02d}:00"
        }
    
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not installed")
    @given(valid_order_strategy())
    def test_property_valid_orders_always_valid(validator, order):
        """Свойство 1: Валидные заказы всегда проходят валидацию"""
        result = validator.validate_order(order)
        assert result["valid"] is True, f"Valid order failed: {result['reasons']}"
        assert 0 <= result["risk_score"] <= 1, "Risk score out of range"
    
    
    @pytest.mark.skipif(not HAS_HYPOTHESIS, reason="Hypothesis not installed")
    @given(st.dictionaries(
        keys=st.text(min_size=3, max_size=20),
        values=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.booleans(),
            st.lists(st.integers(), max_size=10)
        )
    ))
    def test_property_risk_score_in_range(validator, random_order):
        """Свойство 2: Риск-скор всегда в диапазоне [0, 1]"""
        required = ["order_id", "user_id", "items", "total_amount", "created_at"]
        if not all(key in random_order for key in required):
            return
        
        try:
            order = create_order(**random_order)
            result = validator.validate_order(order)
            assert 0 <= result["risk_score"] <= 1, f"Risk score {result['risk_score']} out of range"
        except (KeyError, ValueError, TypeError):
            pass


# ============================================================
# 2.4 Тесты нестабильности и времени
# ============================================================

def test_time_dependent_validation(validator):
    """Проверка зависимости от времени (алкоголь)"""
    now = datetime.now()
    
    allowed_time_order = create_order(
        items=[{"product_id": "P001", "quantity": 1, "price": 100, "category": "Alcohol"}],
        total_amount=100,
        age_verified=True,
        order_time="14:00:00",
        user_created_at=(now - timedelta(days=30)).isoformat()
    )
    
    disallowed_time_order = create_order(
        items=[{"product_id": "P001", "quantity": 1, "price": 100, "category": "Alcohol"}],
        total_amount=100,
        age_verified=True,
        order_time="02:00:00",
        user_created_at=(now - timedelta(days=30)).isoformat()
    )
    
    result_allowed = validator.validate_order(allowed_time_order)
    result_disallowed = validator.validate_order(disallowed_time_order)
    
    assert result_allowed["valid"] is True
    assert result_disallowed["valid"] is False
    assert any("between 08:00 and 23:00" in r for r in result_disallowed["reasons"])


def test_duplicate_orders_stability(validator):
    """Проверка устойчивости к дубликатам заказов"""
    order = create_order(total_amount=1000)
    
    results = []
    for _ in range(10):
        results.append(validator.validate_order(order))
    
    for i in range(1, len(results)):
        assert results[i]["valid"] == results[0]["valid"]
        assert results[i]["risk_score"] == pytest.approx(results[0]["risk_score"], rel=1e-9)
        assert results[i]["reasons"] == results[0]["reasons"]


def test_large_random_batch(validator):
    """Проверка 100 случайных заказов"""
    now = datetime.now()
    
    for i in range(100):
        items_count = random.randint(1, 20)
        items = [
            {
                "product_id": f"P{j:03d}",
                "quantity": random.randint(1, 3),
                "price": random.randint(1, 1000),
                "category": random.choice(["Food", "Electronics", "Books", "Clothing", "Alcohol"])
            }
            for j in range(items_count)
        ]
        
        total = sum(item["quantity"] * item["price"] for item in items)
        
        if random.random() > 0.7:
            items.append({
                "product_id": "P999",
                "quantity": 1,
                "price": 100,
                "category": "Alcohol"
            })
            total += 100
        
        order = create_order(
            items=items,
            total_amount=total,
            age_verified=random.random() > 0.3,
            order_time=f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00",
            user_created_at=(now - timedelta(days=random.randint(0, 30))).isoformat(),
            delivery_country=random.choice(["RU", "US", "UK", "DE"]),
            wallet_country=random.choice(["RU", "US", "UK", "DE"])
        )
        
        result = validator.validate_order(order)
        
        assert isinstance(result["valid"], bool), "valid must be boolean"
        assert isinstance(result["reasons"], list), "reasons must be list"
        assert 0 <= result["risk_score"] <= 1, "risk_score must be in [0, 1]"


def test_risk_score_cap(validator):
    """Проверка что risk_score не превышает 1.0"""
    order = create_order(
        total_amount=100001,
        email_last_changed=(datetime.now() - timedelta(minutes=30)).isoformat(),
        delivery_country="US",
        wallet_country="RU",
        user_created_at=(datetime.now() - timedelta(days=30)).isoformat()
    )
    
    result = validator.validate_order(order)
    assert result["risk_score"] <= 1.0, f"Risk score {result['risk_score']} exceeds 1.0"
    assert result["valid"] is True


# ============================================================
# Запуск тестов
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])