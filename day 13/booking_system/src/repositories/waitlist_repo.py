from typing import List, Optional
from datetime import date, datetime, timedelta
from src.domain.models import WaitlistEntry, WaitlistStatus
from src.repositories.base import BaseRepository


class WaitlistRepository(BaseRepository[WaitlistEntry]):
    """In-Memory репозиторий очереди ожидания"""

    def __init__(self):
        self._storage: dict[int, WaitlistEntry] = {}
        self._next_id = 1

    def get_by_id(self, id: int) -> Optional[WaitlistEntry]:
        return self._storage.get(id)

    def get_all(self, **filters) -> List[WaitlistEntry]:
        result = list(self._storage.values())

        if 'room_id' in filters:
            result = [w for w in result if w.room_id == filters['room_id']]
        if 'status' in filters:
            result = [w for w in result if w.status == filters['status']]
        if 'guest_email' in filters:
            result = [w for w in result if w.guest_email == filters['guest_email']]

        return result

    def get_by_room_and_dates(
        self,
        room_id: int,
        check_in: date,
        check_out: date,
        status: Optional[WaitlistStatus] = None
    ) -> List[WaitlistEntry]:
        """Найти записи в очереди для номера и дат"""
        result = []
        for entry in self._storage.values():
            if entry.room_id != room_id:
                continue
            if status and entry.status != status:
                continue
            if entry.check_in < check_out and entry.check_out > check_in:
                result.append(entry)
        return result

    def get_waiting_by_room_and_dates(
        self,
        room_id: int,
        check_in: date,
        check_out: date
    ) -> List[WaitlistEntry]:
        """Найти активные записи в очереди для номера и дат"""
        return self.get_by_room_and_dates(room_id, check_in, check_out, WaitlistStatus.WAITING)

    def get_expired_entries(self, max_wait_hours: int = 24) -> List[WaitlistEntry]:
        """
        Найти истекшие записи в очереди.
        Запись считается истекшей, если она ждёт больше max_wait_hours часов.
        """
        now = datetime.now()
        result = []
        for entry in self._storage.values():
            if entry.status != WaitlistStatus.WAITING:
                continue
            if (now - entry.created_at) > timedelta(hours=max_wait_hours):
                result.append(entry)
        return result

    def add(self, entry: WaitlistEntry) -> WaitlistEntry:
        entry.id = self._next_id
        # Устанавливаем время истечения (по умолчанию 24 часа)
        if not entry.expires_at:
            entry.expires_at = datetime.now() + timedelta(hours=24)
        self._storage[entry.id] = entry
        self._next_id += 1
        return entry

    def update(self, entry: WaitlistEntry) -> WaitlistEntry:
        if entry.id not in self._storage:
            raise ValueError(f"Waitlist entry with id {entry.id} not found")
        self._storage[entry.id] = entry
        return entry

    def delete(self, id: int) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    def clear(self):
        """Очистить хранилище (для тестов)"""
        self._storage.clear()
        self._next_id = 1