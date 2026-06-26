from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Callable, Dict, Any
import uuid


@dataclass
class DomainEvent:
    """Базовый класс для доменных событий"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    event_type: str = ""
    occurred_at: datetime = field(default_factory=datetime.now)
    aggregate_id: Optional[str] = None


@dataclass
class PaymentCreatedEvent(DomainEvent):
    """Событие: платеж создан"""
    transaction_id: str
    amount: float
    method: str
    
    def __post_init__(self):
        self.event_type = "payment.created"


@dataclass
class PaymentCompletedEvent(DomainEvent):
    """Событие: платеж завершен"""
    transaction_id: str
    amount: float
    commission: float
    net_amount: float
    
    def __post_init__(self):
        self.event_type = "payment.completed"


@dataclass
class PaymentFailedEvent(DomainEvent):
    """Событие: платеж не удался"""
    transaction_id: str
    reason: str
    amount: float
    
    def __post_init__(self):
        self.event_type = "payment.failed"


@dataclass
class RefundCreatedEvent(DomainEvent):
    """Событие: создан возврат"""
    refund_id: str
    transaction_id: str
    refund_amount: float
    fee: float
    reason: str
    
    def __post_init__(self):
        self.event_type = "refund.created"


@dataclass
class RefundCompletedEvent(DomainEvent):
    """Событие: возврат завершен"""
    refund_id: str
    transaction_id: str
    refund_amount: float
    
    def __post_init__(self):
        self.event_type = "refund.completed"


class EventDispatcher:
    """
    Диспетчер доменных событий.
    Реализует паттерн Observer для обработки событий.
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def register(self, event_type: str, handler: Callable) -> None:
        """Зарегистрировать обработчик для события"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def dispatch(self, event: DomainEvent) -> None:
        """Обработать событие всеми зарегистрированными обработчиками"""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            handler(event)
    
    def unregister(self, event_type: str, handler: Callable) -> None:
        """Удалить обработчик"""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass


# Глобальный диспетчер событий
_event_dispatcher = EventDispatcher()


def get_event_dispatcher() -> EventDispatcher:
    """Получить глобальный диспетчер событий"""
    return _event_dispatcher


class EventHandler:
    """Базовый класс для обработчиков событий"""
    
    def handle(self, event: DomainEvent) -> None:
        """Обработать событие"""
        raise NotImplementedError