"""
Вариант 3: DataFrame (pandas) с ошибками

Типы ошибок:
1. Обращение к несуществующей колонке (KeyError)
2. Деление на ноль в apply()
3. Кеширование результатов без LRU (утечка памяти)
4. Использование .loc с ошибкой
"""

import pandas as pd
import numpy as np
import time
import tracemalloc
from functools import lru_cache
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Глобальный кеш — потенциальная утечка памяти
RESULT_CACHE = {}


def calculate_booking_price(row):
    """
    Расчет стоимости бронирования с логическими ошибками.
    
    Ошибка 1: Деление на ноль при nights = 0
    Ошибка 2: Неправильная формула скидки
    """
    try:
        price_per_night = row['price_per_night']
        nights = row['nights']
        is_vip = row.get('vip', False)
        season = row.get('season', 'normal')
        
        # Ошибка 1: Деление на ноль!
        base_price = price_per_night * nights
        
        # Сезонный коэффициент
        season_coeff = {
            'high': 1.3,
            'normal': 1.0,
            'low': 0.8
        }.get(season, 1.0)
        
        # Ошибка 2: Неправильный расчет скидки (должно быть price * (1 - discount))
        if is_vip:
            # Ошибка: скидка 15% применяется неправильно
            discount = 0.15
            final_price = base_price * season_coeff - (base_price * season_coeff * discount)
        else:
            final_price = base_price * season_coeff
        
        # Ошибка 3: Неправильная обработка nights = 0
        # Ошибка 4: Деление на ноль!
        avg_price_per_night = final_price / nights if nights > 0 else 0
        
        # Кеширование без ограничения размера
        cache_key = f"{row.get('booking_id', 'unknown')}_{nights}"
        RESULT_CACHE[cache_key] = {
            'final_price': final_price,
            'avg_price_per_night': avg_price_per_night,
            'discount': discount if is_vip else 0
        }
        
        return final_price
        
    except Exception as e:
        logger.error(f"Ошибка в calculate_booking_price: {e}")
        logger.error(f"Данные строки: {row.to_dict() if hasattr(row, 'to_dict') else row}")
        raise


def process_booking_data(df):
    """
    Основная функция обработки данных с ошибками.
    
    Ошибка 5: Обращение к несуществующей колонке 'total_price'
    Ошибка 6: Использование .loc с ошибкой
    """
    logger.info(f"Начало обработки {len(df)} записей")
    
    # Ошибка 5: Колонка 'total_price' не существует
    df['calculated_price'] = df.apply(calculate_booking_price, axis=1)
    
    # Ошибка 6: Неправильное использование .loc
    # Попытка обратиться к несуществующей колонке
    df.loc[df['vip'] == True, 'vip_discount'] = df['calculated_price'] * 0.15
    
    # Ошибка 7: Попытка использовать .loc с булевым массивом неправильной длины
    mask = df['nights'] > 5
    df.loc[mask, 'long_stay_discount'] = df.loc[mask, 'calculated_price'] * 0.1
    
    # Агрегация с ошибкой
    total_revenue = df['calculated_price'].sum()
    
    return df, total_revenue


def create_test_data(size=1000):
    """Создание тестовых данных с ошибками"""
    np.random.seed(42)
    
    # Ошибка 8: В некоторых записях отсутствует колонка 'price_per_night'
    # Ошибка 9: В некоторых записях nights = 0
    data = {
        'booking_id': range(1, size + 1),
        'price_per_night': np.random.uniform(50, 500, size),
        'nights': np.random.randint(0, 14, size),  # включая 0!
        'vip': np.random.choice([True, False], size, p=[0.2, 0.8]),
        'season': np.random.choice(['high', 'normal', 'low'], size, p=[0.3, 0.5, 0.2])
    }
    
    df = pd.DataFrame(data)
    
    # Добавляем строки с отсутствующими данными
    if size > 10:
        df.loc[5:7, 'price_per_night'] = None  # Ошибка 8
        df.loc[8:10, 'nights'] = 0  # Ошибка 9
    
    # Ошибка 10: Дублирование booking_id
    df.loc[1, 'booking_id'] = 1
    
    return df


def main():
    """Основная функция"""
    logger.info("=" * 60)
    logger.info("Запуск программы с ошибками (Вариант 3)")
    
    # Включаем tracemalloc для отслеживания памяти
    tracemalloc.start()
    
    # Создаем тестовые данные
    df = create_test_data(100)
    logger.info(f"Создано {len(df)} записей")
    
    try:
        # Обработка данных
        result_df, total = process_booking_data(df)
        logger.info(f"Обработка завершена. Общая выручка: {total:.2f}")
        logger.info(f"Результат:\n{result_df.head(10)}")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    # Анализ памяти
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    logger.info("\n" + "=" * 60)
    logger.info("ТОП-10 СТРОК ПО ПОТРЕБЛЕНИЮ ПАМЯТИ:")
    for stat in top_stats[:10]:
        logger.info(f"  {stat}")
    
    logger.info(f"\nРазмер кеша: {len(RESULT_CACHE)} записей")
    logger.info(f"Размер кеша в памяти: {sum(len(str(v)) for v in RESULT_CACHE.values())} байт")


if __name__ == "__main__":
    main()