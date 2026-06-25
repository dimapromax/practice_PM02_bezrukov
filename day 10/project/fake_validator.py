
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import random
import json
from enum import Enum


class OrderCategory(Enum):
    FOOD = "Food"
    ELECTRONICS = "Electronics"
    ALCOHOL = "Alcohol"
    CLOTHING = "Clothing"
    BOOKS = "Books"


@dataclass
class OrderItem:
    """Товар в заказе"""
    product_id: str
    quantity: int
    price: float
    category: str

    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("Quantity must be >= 1")
        if self.price < 0:
            raise ValueError("Price must be >= 0")
        if self.category not in [c.value for c in OrderCategory]:
            raise ValueError(f"Invalid category: {self.category}")


@dataclass
class Order:
    """Входные данные заказа"""
    order_id: str
    user_id: str
    items: List[OrderItem]
    total_amount: float
    created_at: datetime
    user_created_at: datetime
    user_email: str
    email_last_changed: Optional[datetime]
    delivery_country: str
    wallet_country: str
    age_verified: bool
    order_time: str

    def __post_init__(self):
        if self.total_amount < 0:
            raise ValueError("Total amount must be >= 0")
        if len(self.items) == 0:
            raise ValueError("Order must have at least one item")
        if len(self.items) > 50:
            raise ValueError("Order has too many items (max 50)")
        if self.delivery_country not in self._get_countries():
            raise ValueError(f"Invalid delivery country: {self.delivery_country}")
        if self.wallet_country not in self._get_countries():
            raise ValueError(f"Invalid wallet country: {self.wallet_country}")

    @staticmethod
    def _get_countries():
        return ["RU", "US", "UK", "DE", "FR", "IT", "ES", "CN", "JP", "BR"]


@dataclass
class ValidationResult:
    """Результат валидации"""
    valid: bool
    reasons: List[str]
    risk_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "reasons": self.reasons,
            "risk_score": self.risk_score
        }


class FakeValidator:
    """
    Эталонная реализация валидатора заказов.
    Строго следует спецификации.
    """
    
    # Константы правил
    MAX_ORDER_AMOUNT = 1_000_000
    MIN_ORDER_AMOUNT = 0
    NEW_USER_THRESHOLD_DAYS = 7
    NEW_USER_MAX_AMOUNT = 15_000
    MAX_ITEMS = 50
    HIGH_RISK_THRESHOLD = 100_000
    EMAIL_CHANGE_WINDOW_HOURS = 1
    ALCOHOL_START_HOUR = 8
    ALCOHOL_END_HOUR = 23
    
    # Сообщения об ошибках
    ERROR_AMOUNT = "Total amount must be between 0 and 1,000,000"
    ERROR_NEW_USER = "New users (registered < 7 days) cannot order more than 15,000"
    ERROR_TOO_MANY_ITEMS = "Order has too many items (max 50)"
    ERROR_ALCOHOL_AGE = "Alcohol requires age verification"
    ERROR_ALCOHOL_TIME = "Alcohol can only be ordered between 08:00 and 23:00"
    
    def __init__(self, chaos_mode: bool = False, chaos_probability: float = 0.05):
        """
        Args:
            chaos_mode: Включает режим хаоса (случайные ошибки)
            chaos_probability: Вероятность случайной ошибки (0-1)
        """
        self.chaos_mode = chaos_mode
        self.chaos_probability = chaos_probability
        self._validation_count = 0
    
    def validate_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Основной метод валидации заказа.
        
        Args:
            order_data: Словарь с данными заказа
            
        Returns:
            Dict с ключами: valid, reasons, risk_score
        """
        self._validation_count += 1
        
        # Режим хаоса: случайный сбой
        if self.chaos_mode and random.random() < self.chaos_probability:
            return self._chaos_response()
        
        try:
            # Преобразование входных данных в объект Order
            order = self._parse_order(order_data)
        except (ValueError, KeyError, TypeError) as e:
            return {
                "valid": False,
                "reasons": [f"Invalid input: {str(e)}"],
                "risk_score": 0.0
            }
        
        # Валидация по правилам
        reasons = []
        risk_score = self._calculate_base_risk(order)
        
        # Правило 1: Проверка суммы
        if not (self.MIN_ORDER_AMOUNT < order.total_amount < self.MAX_ORDER_AMOUNT):
            reasons.append(self.ERROR_AMOUNT)
        
        # Правило 2: Новый пользователь
        if self._is_new_user(order.user_created_at):
            if order.total_amount > self.NEW_USER_MAX_AMOUNT:
                reasons.append(self.ERROR_NEW_USER)
        
        # Правило 3: Количество позиций
        if len(order.items) > self.MAX_ITEMS:
            reasons.append(self.ERROR_TOO_MANY_ITEMS)
        
        # Правило 4: Алкоголь
        alcohol_items = [item for item in order.items if item.category == OrderCategory.ALCOHOL.value]
        if alcohol_items:
            if not order.age_verified:
                reasons.append(self.ERROR_ALCOHOL_AGE)
            if not self._is_alcohol_time_allowed(order.order_time):
                reasons.append(self.ERROR_ALCOHOL_TIME)
        
        # Правило 5: Риск-скоринг (дополнительные факторы)
        risk_score = self._apply_risk_factors(risk_score, order)
        
        return {
            "valid": len(reasons) == 0,
            "reasons": reasons,
            "risk_score": min(1.0, max(0.0, risk_score))
        }
    
    def _parse_order(self, data: Dict[str, Any]) -> Order:
        """Парсинг входных данных в объект Order"""
        items = []
        for item_data in data.get("items", []):
            items.append(OrderItem(
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                price=item_data["price"],
                category=item_data["category"]
            ))
        
        return Order(
            order_id=data["order_id"],
            user_id=data["user_id"],
            items=items,
            total_amount=data["total_amount"],
            created_at=self._parse_datetime(data["created_at"]),
            user_created_at=self._parse_datetime(data.get("user_created_at", data["created_at"])),
            user_email=data.get("user_email", ""),
            email_last_changed=self._parse_datetime(data.get("email_last_changed")) if data.get("email_last_changed") else None,
            delivery_country=data.get("delivery_country", "RU"),
            wallet_country=data.get("wallet_country", "RU"),
            age_verified=data.get("age_verified", False),
            order_time=data.get("order_time", "12:00:00")
        )
    
    def _parse_datetime(self, value: Any) -> datetime:
        """Парсинг даты/времени из строки или datetime"""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Поддержка форматов ISO
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        raise ValueError(f"Invalid datetime: {value}")
    
    def _is_new_user(self, user_created_at: datetime) -> bool:
        """Проверка, является ли пользователь новым (< 7 дней)"""
        now = datetime.now(user_created_at.tzinfo)
        return (now - user_created_at).days < self.NEW_USER_THRESHOLD_DAYS
    
    def _is_alcohol_time_allowed(self, time_str: str) -> bool:
        """Проверка, разрешено ли время для алкоголя"""
        try:
            parts = time_str.split(':')
            hour = int(parts[0])
            return self.ALCOHOL_START_HOUR <= hour < self.ALCOHOL_END_HOUR
        except (ValueError, IndexError):
            return False
    
    def _calculate_base_risk(self, order: Order) -> float:
        """Расчёт базового риска (0.1 - стандартный)"""
        return 0.1
    
    def _apply_risk_factors(self, risk: float, order: Order) -> float:
        """Применение факторов риска"""
        # Фактор 1: Высокая сумма
        if order.total_amount > self.HIGH_RISK_THRESHOLD:
            risk = 0.9
        
        # Фактор 2: Смена email за последний час
        if order.email_last_changed:
            time_diff = datetime.now(order.email_last_changed.tzinfo) - order.email_last_changed
            if time_diff.total_seconds() < self.EMAIL_CHANGE_WINDOW_HOURS * 3600:
                risk += 0.2
        
        # Фактор 3: Разные страны
        if order.delivery_country != order.wallet_country:
            risk += 0.3
        
        return min(1.0, risk)
    
    def _chaos_response(self) -> Dict[str, Any]:
        """Генерация хаотичного ответа для проверки устойчивости тестов"""
        chaos_types = [
            {"valid": False, "reasons": ["Chaos mode: random failure"], "risk_score": 0.5},
            {"valid": True, "reasons": [], "risk_score": 0.5},
            {"valid": False, "reasons": ["Chaos mode: unexpected error"], "risk_score": 0.0},
            {"valid": True, "reasons": [], "risk_score": 1.0},
        ]
        return random.choice(chaos_types)
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика валидаций"""
        return {
            "total_validations": self._validation_count
        }


# Функция для создания валидатора (фабрика)
def create_validator(chaos_mode: bool = False, chaos_probability: float = 0.05) -> FakeValidator:
    """Фабрика для создания экземпляра валидатора"""
    return FakeValidator(chaos_mode=chaos_mode, chaos_probability=chaos_probability)


# Пример использования
if __name__ == "__main__":
    validator = create_validator()
    
    # Тестовый заказ
    test_order = {
        "order_id": "ORD-001",
        "user_id": "USR-001",
        "items": [
            {"product_id": "P001", "quantity": 2, "price": 500, "category": "Food"}
        ],
        "total_amount": 1000,
        "created_at": datetime.now().isoformat(),
        "user_created_at": (datetime.now() - timedelta(days=30)).isoformat(),
        "user_email": "user@example.com",
        "email_last_changed": (datetime.now() - timedelta(hours=2)).isoformat(),
        "delivery_country": "RU",
        "wallet_country": "RU",
        "age_verified": False,
        "order_time": "10:00:00"
    }
    
    result = validator.validate_order(test_order)
    print(json.dumps(result, indent=2))