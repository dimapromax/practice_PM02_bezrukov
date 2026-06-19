from datetime import date
from typing import Optional, Dict

from src.domain.models import Room
from src.domain.exceptions import InvalidDatesError


class PricingService:

    def __init__(self, seasonal_coefficients: Optional[Dict[int, float]] = None):
    
        self.seasonal_coefficients = seasonal_coefficients or {
            # Месяц: коэффициент
            6: 1.2,   # Июнь
            7: 1.5,   # Июль
            8: 1.5,   # Август
            12: 1.3,  # Декабрь (Новый год)
            1: 1.1,   # Январь
            2: 1.05,  # Февраль (23 февраля)
            3: 1.05,  # Март (8 марта)
            5: 1.1,   # Май (праздники)
        }

    def calculate_price(
        self,
        room: Room,
        check_in: date,
        check_out: date
    ) -> float:
        """
        Рассчитать стоимость бронирования с учётом сезонных коэффициентов
        и скидок за длительное бронирование.
        """
        nights = (check_out - check_in).days
        if nights <= 0:
            raise InvalidDatesError("Количество ночей должно быть больше 0")

        total = 0.0
        current = check_in

        # По дням рассчитываем стоимость с учётом сезонности
        for _ in range(nights):
            month = current.month
            coefficient = self.seasonal_coefficients.get(month, 1.0)
            total += room.price_per_night * coefficient
            current = date(current.year, current.month + 1, 1) if current.month < 12 \
                else date(current.year + 1, 1, 1)

        # Скидка за длительное бронирование
        if nights >= 7:
            total *= 0.95  # 5% скидка
        if nights >= 14:
            total *= 0.9   # дополнительная скидка (всего ~14.5%)
        if nights >= 21:
            total *= 0.85  # дополнительная скидка (всего ~27%)

        return round(total, 2)