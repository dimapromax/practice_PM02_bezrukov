from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Базовый класс репозитория"""

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Получить запись по ID"""
        pass

    @abstractmethod
    def get_all(self, **filters) -> List[T]:
        """Получить все записи с фильтрацией"""
        pass

    @abstractmethod
    def add(self, entity: T) -> T:
        """Добавить запись"""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Обновить запись"""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Удалить запись"""
        pass