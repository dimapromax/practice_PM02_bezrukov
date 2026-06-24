import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Фикстура для TestClient FastAPI"""
    # Очищаем dependency_overrides перед каждым тестом
    app.dependency_overrides.clear()
    return TestClient(app)

@pytest.fixture
def sample_order_data():
    """Фикстура с примером данных заказа"""
    return {
        "id": 1,
        "total": 100.0,
        "status": "PENDING"
    }

@pytest.fixture
def admin_user():
    """Фикстура с данными администратора"""
    return {
        "id": 1,
        "username": "admin",
        "role": "admin"
    }

@pytest.fixture
def regular_user():
    """Фикстура с данными обычного пользователя"""
    return {
        "id": 2,
        "username": "user",
        "role": "user"
    }