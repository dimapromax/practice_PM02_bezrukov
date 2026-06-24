import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

from app.models import Base, Order, OrderItem
from app.repositories import OrderRepository


@pytest.fixture(scope="function")
def db_session():
    """
    Фикстура, создающая in-memory SQLite БД и сессию.
    Scope function означает, что БД создаётся заново для каждого теста.
    """
    # Создаём движок для in-memory SQLite
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Создаём все таблицы
    Base.metadata.create_all(engine)
    
    # Создаём фабрику сессий
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        # Откатываем изменения и закрываем сессию
        try:
            session.rollback()
        except:
            pass
        session.close()
        # Закрываем соединение с БД
        engine.dispose()
        # Удаляем таблицы
        Base.metadata.drop_all(engine)


@pytest.fixture
def repository(db_session):
    """Фикстура, возвращающая репозиторий с тестовой сессией."""
    return OrderRepository(db_session)


@pytest.fixture
def sample_order_data():
    """Фикстура с данными для создания тестового заказа."""
    return {
        "customer_name": "Иван Петров",
        "delivery_address": "г. Москва, ул. Тверская, д. 1",
        "total_amount": 1000.00,
        "items": [
            {"product_name": "Товар 1", "quantity": 2, "price": 300.00},
            {"product_name": "Товар 2", "quantity": 1, "price": 400.00}
        ]
    }


@pytest.fixture
def sample_order(db_session, sample_order_data):
    """Фикстура, создающая и возвращающая тестовый заказ."""
    repo = OrderRepository(db_session)
    return repo.create(sample_order_data)