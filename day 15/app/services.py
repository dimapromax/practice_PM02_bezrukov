from typing import Optional

class Order:
    def __init__(self, id: int, total: float, status: str = "PENDING"):
        self.id = id
        self.total = total
        self.status = status

def get_order(order_id: int) -> Optional[Order]:
    """Заглушка сервиса получения заказа"""
    # В реальном приложении здесь был бы запрос к БД
    return Order(id=order_id, total=100.0, status="PENDING")