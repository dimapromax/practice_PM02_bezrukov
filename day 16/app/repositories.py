from datetime import datetime
from typing import List, Optional, Dict, Any
import httpx

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import Order, OrderItem
from app.exceptions import EntityNotFoundException, DeliveryCalculationException


class OrderRepository:
    """Репозиторий для управления заказами."""
    
    def __init__(self, session: Session):
       
        self.session = session
    
    def create(self, order_data: Dict[str, Any]) -> Order:
       
        # Извлекаем данные позиций
        items_data = order_data.pop('items', [])
        
        # Создаём заказ
        order = Order(**order_data)
        self.session.add(order)
        
        # Создаём позиции и добавляем через отношение
        for item_data in items_data:
            item = OrderItem(**item_data)
            order.items.append(item)  # Важно: добавляем через relationship
        
        # Сохраняем все изменения
        try:
            self.session.commit()
            self.session.refresh(order)
        except Exception:
            self.session.rollback()
            raise
        
        return order
    
    def find_by_id(self, order_id: int) -> Optional[Order]:
        """Возвращает заказ по ID."""
        return self.session.query(Order).filter(Order.id == order_id).first()
    
    def find_all_by_status(self, status: str) -> List[Order]:
        """Возвращает список заказов с указанным статусом."""
        return self.session.query(Order).filter(Order.status == status).all()
    
    def update_status(self, order_id: int, new_status: str) -> Order:
        """Обновляет статус заказа."""
        order = self.find_by_id(order_id)
        if not order:
            raise EntityNotFoundException("Order", order_id)
        
        order.status = new_status
        self.session.commit()
        self.session.refresh(order)
        
        return order
    
    def delete(self, order_id: int) -> None:
        """Жёстко удаляет заказ и все его позиции."""
        order = self.find_by_id(order_id)
        if order:
            self.session.delete(order)
            self.session.commit()
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """Возвращает заказы в указанном временном интервале."""
        return self.session.query(Order).filter(
            and_(Order.created_at >= start_date, Order.created_at <= end_date)
        ).all()
    
    def get_total_amount_for_order(self, order_id: int) -> float:
        """Вычисляет сумму всех позиций заказа."""
        result = self.session.query(
            func.sum(OrderItem.quantity * OrderItem.price)
        ).filter(OrderItem.order_id == order_id).scalar()
        
        return float(result) if result is not None else 0.0
    
    def calculate_delivery_cost(self, order_id: int) -> float:
        """Рассчитывает стоимость доставки через внешний API."""
        order = self.find_by_id(order_id)
        if not order:
            raise EntityNotFoundException("Order", order_id)
        
        total_weight = sum(item.quantity * 0.5 for item in order.items)
        
        payload = {
            "address": order.delivery_address,
            "weight": total_weight
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    "https://api.delivery.com/calculate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return float(data.get("cost", 0.0))
        except httpx.HTTPStatusError as e:
            raise DeliveryCalculationException(
                f"API returned status {e.response.status_code}",
                status_code=e.response.status_code
            )
        except httpx.RequestError as e:
            raise DeliveryCalculationException(f"Network error: {str(e)}")
        except (KeyError, ValueError) as e:
            raise DeliveryCalculationException(f"Invalid response format: {str(e)}")