import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from fake_validator import FakeValidator, create_validator


@pytest.fixture(scope="session")
def validator_config() -> Dict[str, Any]:
    """Конфигурация валидатора для всей сессии"""
    return {
        "chaos_mode": False,
        "chaos_probability": 0.05
    }


@pytest.fixture
def validator(validator_config) -> FakeValidator:
    """Создание валидатора"""
    return create_validator(
        chaos_mode=validator_config["chaos_mode"],
        chaos_probability=validator_config["chaos_probability"]
    )


@pytest.fixture
def chaos_validator() -> FakeValidator:
    """Валидатор с режимом хаоса"""
    return create_validator(chaos_mode=True, chaos_probability=0.1)


@pytest.fixture
def now() -> datetime:
    """Текущее время"""
    return datetime.now()


@pytest.fixture
def base_order(now) -> Dict[str, Any]:
    """Базовый корректный заказ"""
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


def pytest_configure(config):
    """Настройка маркеров"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "chaos: tests that use chaos mode"
    )