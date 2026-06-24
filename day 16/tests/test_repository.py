import pytest
import httpx
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError, PendingRollbackError

from app.models import Order, OrderItem
from app.exceptions import EntityNotFoundException, DeliveryCalculationException


class TestOrderRepository:
    """Тесты для OrderRepository."""
    
    def test_create_order(self, repository, db_session, sample_order_data):
        """Тест создания заказа."""
        # Act
        order = repository.create(sample_order_data)
        
        # Assert
        assert order.id is not None
        assert order.customer_name == sample_order_data["customer_name"]
        assert order.delivery_address == sample_order_data["delivery_address"]
        assert order.total_amount == sample_order_data["total_amount"]
        assert order.status == "PENDING"
        assert len(order.items) == 2
        
        # Проверяем, что данные сохранились в БД
        saved_order = db_session.query(Order).filter(Order.id == order.id).first()
        assert saved_order is not None
        assert saved_order.customer_name == order.customer_name
        
        # Проверяем позиции
        saved_items = db_session.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).all()
        assert len(saved_items) == 2
    
    def test_find_by_id_existing(self, repository, sample_order):
        """Тест поиска существующего заказа по ID."""
        # Act
        found_order = repository.find_by_id(sample_order.id)
        
        # Assert
        assert found_order is not None
        assert found_order.id == sample_order.id
        assert found_order.customer_name == sample_order.customer_name
    
    def test_find_by_id_non_existing(self, repository):
        """Тест поиска несуществующего заказа."""
        # Act
        found_order = repository.find_by_id(999)
        
        # Assert
        assert found_order is None
    
    @pytest.mark.parametrize("status", ["PENDING", "PAID", "SHIPPED", "CANCELLED"])
    def test_find_all_by_status(self, repository, db_session, status):
        """Тест поиска заказов по статусу (параметризованный)."""
        # Arrange - создаём заказы с разными статусами
        order_data = {
            "customer_name": "Тестовый клиент",
            "delivery_address": "Тестовый адрес",
            "total_amount": 100.00,
            "items": [{"product_name": "Тестовый товар", "quantity": 1, "price": 100.00}]
        }
        
        # Создаём заказ с нужным статусом
        order1 = repository.create(order_data)
        # Обновляем статус через репозиторий
        repository.update_status(order1.id, status)
        
        # Создаём заказ с другим статусом
        order_data2 = order_data.copy()
        order_data2["customer_name"] = "Другой клиент"
        order2 = repository.create(order_data2)
        other_status = "PAID" if status != "PAID" else "PENDING"
        repository.update_status(order2.id, other_status)
        
        # Act
        found_orders = repository.find_all_by_status(status)
        
        # Assert
        assert len(found_orders) >= 1
        for order in found_orders:
            assert order.status == status
        
        # Проверяем, что заказ с другим статусом не попал в выборку
        other_orders = repository.find_all_by_status(other_status)
        for order in other_orders:
            assert order.status == other_status
    
    def test_update_status_existing(self, repository, sample_order):
        """Тест обновления статуса существующего заказа."""
        # Act
        updated_order = repository.update_status(sample_order.id, "PAID")
        
        # Assert
        assert updated_order.status == "PAID"
        assert updated_order.id == sample_order.id
        
        # Проверяем, что статус обновился в БД
        db_order = repository.find_by_id(sample_order.id)
        assert db_order.status == "PAID"
    
    def test_update_status_non_existing(self, repository):
        """Тест обновления статуса несуществующего заказа."""
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            repository.update_status(999, "PAID")
        
        assert "Order with id 999 not found" in str(exc_info.value)
    
    def test_delete_order(self, repository, db_session, sample_order):
        """Тест удаления заказа."""
        # Arrange - сохраняем ID
        order_id = sample_order.id
        
        # Act
        repository.delete(order_id)
        
        # Assert
        deleted_order = repository.find_by_id(order_id)
        assert deleted_order is None
        
        # Проверяем, что позиции тоже удалены
        items = db_session.query(OrderItem).filter(
            OrderItem.order_id == order_id
        ).all()
        assert len(items) == 0
    
    def test_find_by_date_range(self, repository, db_session):
        """Тест поиска заказов по диапазону дат."""
        # Arrange
        now = datetime.now()
        
        # Создаём заказы с разными датами
        order_data = {
            "customer_name": "Клиент",
            "delivery_address": "Адрес",
            "total_amount": 100.00,
            "items": [{"product_name": "Товар", "quantity": 1, "price": 100.00}]
        }
        
        # Заказ в прошлом (2 дня назад)
        past_order = repository.create(order_data)
        past_order.created_at = now - timedelta(days=2)
        db_session.commit()
        db_session.refresh(past_order)
        
        # Заказ сегодня
        today_order = repository.create(order_data)
        today_order.created_at = now
        db_session.commit()
        db_session.refresh(today_order)
        
        # Заказ в будущем (2 дня вперёд)
        future_order = repository.create(order_data)
        future_order.created_at = now + timedelta(days=2)
        db_session.commit()
        db_session.refresh(future_order)
        
        # Act
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)
        found_orders = repository.find_by_date_range(start_date, end_date)
        
        # Assert
        found_ids = [o.id for o in found_orders]
        assert today_order.id in found_ids
        assert past_order.id not in found_ids
        assert future_order.id not in found_ids
    
    def test_get_total_amount_for_order(self, repository, sample_order):
        """Тест подсчёта суммы заказа."""
        # Act
        total = repository.get_total_amount_for_order(sample_order.id)
        
        # Assert
        expected_total = sum(item.quantity * item.price for item in sample_order.items)
        assert total == expected_total
    
    def test_get_total_amount_for_empty_order(self, repository, db_session):
        """Тест подсчёта суммы для заказа без позиций."""
        # Arrange
        order_data = {
            "customer_name": "Клиент",
            "delivery_address": "Адрес",
            "total_amount": 0.00,
            "items": []
        }
        order = repository.create(order_data)
        
        # Act
        total = repository.get_total_amount_for_order(order.id)
        
        # Assert
        assert total == 0.0
    
    def test_transaction_rollback_on_invalid_data(self, repository, db_session):
        """Тест отката транзакции при некорректных данных."""
        # Arrange
        order_data = {
            "customer_name": "Клиент",
            "delivery_address": "Адрес",
            "total_amount": 100.00,
            "items": [
                {"product_name": "Товар", "quantity": -1, "price": 100.00}  # Отрицательное количество
            ]
        }
        
        # Act & Assert
        with pytest.raises(Exception):  # SQLAlchemy выбросит исключение
            repository.create(order_data)
        
        # Откатываем сессию, если она в состоянии ошибки
        try:
            db_session.rollback()
        except:
            pass
        
        # Проверяем, что заказ не был создан
        orders = db_session.query(Order).all()
        assert len(orders) == 0
        
        # Проверяем, что позиции не были созданы
        items = db_session.query(OrderItem).all()
        assert len(items) == 0
    
    def test_calculate_delivery_cost_success(self, repository, sample_order, httpx_mock):
        """Тест успешного расчёта стоимости доставки."""
        # Arrange
        expected_cost = 150.0
        httpx_mock.add_response(
            url="https://api.delivery.com/calculate",
            method="POST",
            json={"cost": expected_cost},
            status_code=200
        )
        
        # Act
        cost = repository.calculate_delivery_cost(sample_order.id)
        
        # Assert
        assert cost == expected_cost
        
        # Проверяем, что запрос был отправлен с правильными данными
        request = httpx_mock.get_requests()[0]
        # Используем request.content для получения тела запроса
        import json
        request_data = json.loads(request.content)
        assert request_data["address"] == sample_order.delivery_address
        expected_weight = sum(item.quantity * 0.5 for item in sample_order.items)
        assert request_data["weight"] == expected_weight
    
    def test_calculate_delivery_cost_order_not_found(self, repository):
        """Тест расчёта доставки для несуществующего заказа."""
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            repository.calculate_delivery_cost(999)
        
        assert "Order with id 999 not found" in str(exc_info.value)
    
    def test_calculate_delivery_cost_api_error(self, repository, sample_order, httpx_mock):
        """Тест ошибки внешнего API."""
        # Arrange
        httpx_mock.add_response(
            url="https://api.delivery.com/calculate",
            method="POST",
            status_code=500,
            text="Internal Server Error"
        )
        
        # Act & Assert
        with pytest.raises(DeliveryCalculationException) as exc_info:
            repository.calculate_delivery_cost(sample_order.id)
        
        assert "API returned status 500" in str(exc_info.value)
    
    def test_calculate_delivery_cost_network_error(self, repository, sample_order, httpx_mock):
        """Тест сетевой ошибки при запросе к API."""
        # Arrange
        httpx_mock.add_exception(
            url="https://api.delivery.com/calculate",
            method="POST",
            exception=httpx.TimeoutException("Connection timeout")
        )
        
        # Act & Assert
        with pytest.raises(DeliveryCalculationException) as exc_info:
            repository.calculate_delivery_cost(sample_order.id)
        
        assert "Network error" in str(exc_info.value)
    
    def test_calculate_delivery_cost_invalid_response(self, repository, sample_order, httpx_mock):
        """Тест некорректного ответа от API."""
        # Arrange
        httpx_mock.add_response(
            url="https://api.delivery.com/calculate",
            method="POST",
            json={"invalid": "response"},
            status_code=200
        )
        
        # Act & Assert
        with pytest.raises(DeliveryCalculationException) as exc_info:
            repository.calculate_delivery_cost(sample_order.id)
        
        assert "Invalid response format" in str(exc_info.value)