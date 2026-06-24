# README.md - День 16

## Описание проекта

Микросервис управления заказами с реализацией репозитория и интеграционными тестами.

## Технологии

- Python 3.10+
- SQLAlchemy 2.0+
- pytest, pytest-httpx, pytest-cov
- httpx

## Структура проекта

```
day 16/
├── app/
│   ├── __init__.py
│   ├── exceptions.py      # Исключения
│   ├── models.py          # Модели SQLAlchemy
│   └── repositories.py    # Репозиторий
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Фикстуры
│   └── test_repository.py # Тесты
├── requirements.txt
└── README.md
```

## Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск тестов
pytest tests/ -v --cov=app --cov-report=term-missing

# Генерация HTML отчёта
pytest tests/ --cov=app --cov-report=html
```

## Модели данных

### Order (Заказ)
- id: Integer (PK)
- status: String (PENDING, PAID, SHIPPED, CANCELLED)
- created_at: DateTime
- customer_name: String
- delivery_address: String
- total_amount: Numeric

### OrderItem (Позиция заказа)
- id: Integer (PK)
- order_id: Integer (FK -> orders.id)
- product_name: String
- quantity: Integer
- price: Numeric

## Методы репозитория

- create(order_data) - создание заказа
- find_by_id(order_id) - поиск по ID
- find_all_by_status(status) - поиск по статусу
- update_status(order_id, new_status) - обновление статуса
- delete(order_id) - удаление заказа
- find_by_date_range(start, end) - поиск по датам
- get_total_amount_for_order(order_id) - подсчёт суммы
- calculate_delivery_cost(order_id) - расчёт доставки

## Тесты

### Интеграционные тесты
- Создание заказа
- Поиск по ID (существующий/несуществующий)
- Поиск по статусу (параметризованный)
- Обновление статуса
- Удаление заказа (каскадное)
- Поиск по диапазону дат
- Подсчёт суммы заказа
- Транзакционность (откат)

### Контрактные тесты (внешний API)
- Успешный ответ
- Ошибка сервера (500)
- Сетевая ошибка
- Некорректный ответ

## Покрытие кода

```
Name                     Stmts   Miss  Cover
--------------------------------------------
app/__init__.py              0      0   100%
app/exceptions.py            9      0   100%
app/models.py               29      1    97%
app/repositories.py         64      0   100%
--------------------------------------------
TOTAL                      102      1    99%
```

## Обработка ошибок

- EntityNotFoundException - сущность не найдена
- DeliveryCalculationException - ошибка расчёта доставки

## Запуск через bat-файл

```batch
run_tests.bat
```

## Команды для CMD

```cmd
cd C:\Users\Student\Desktop\practice_PM02_bezrukov\day 16
set PYTHONPATH=%CD%
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Результат

- ✅ 19 тестов проходят успешно
- ✅ Покрытие кода 99%
- ✅ Все методы репозитория реализованы
- ✅ Интеграционные и контрактные тесты написаны

---

## Контрольные вопросы для допуска

### Базовые вопросы по pytest и тестированию

**1. Чем отличается pytest от unittest?**

pytest имеет более простой синтаксис, не требует наследования от TestCase, использует обычные assert, поддерживает фикстуры и параметризацию. unittest встроен в Python, требует наследования и специальных assert методов.

**2. Что такое @pytest.mark.parametrize?**

Декоратор для параметризации тестов. Позволяет запускать один тест с разными наборами данных.

Пример:
```python
@pytest.mark.parametrize("status", ["PENDING", "PAID", "SHIPPED"])
def test_find_by_status(status):
    assert status in ["PENDING", "PAID", "SHIPPED"]
```

**3. В чем разница между mock.Mock() и mock.patch()?**

- Mock() - создаёт объект-заглушку для замены реального объекта
- patch() - контекстный менеджер/декоратор для замены объектов в определённом контексте с автоматическим восстановлением

**4. Как тестировать асинхронные функции в Python?**

Использовать pytest-asyncio и маркер @pytest.mark.asyncio

Пример:
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

**5. Что такое coverage.py и какой порог считается хорошим?**

Инструмент для измерения покрытия кода тестами. Хорошим считается покрытие 80-90%, отличным - 95-100%.

### Вопросы по SQLAlchemy и интеграционному тестированию

**6. Что такое паттерн Repository и зачем он используется?**

Repository - паттерн, предоставляющий абстракцию над хранилищем данных. Используется для изоляции логики доступа к данным, упрощения тестирования и смены БД.

**7. Как в SQLAlchemy организовать транзакцию и почему важно тестировать транзакционность?**

```python
session.begin()
try:
    session.add(object)
    session.commit()
except:
    session.rollback()
    raise
```

Тестирование транзакционности важно для проверки целостности данных и отката при ошибках.

**8. Как проверить, что при создании заказа с некорректными данными транзакция откатывается?**

```python
def test_transaction_rollback(repository, db_session):
    with pytest.raises(Exception):
        repository.create(invalid_data)
    
    # Проверяем, что данные не сохранились
    assert db_session.query(Order).count() == 0
```

**9. Как с помощью pytest-httpx эмулировать ответ внешнего API?**

```python
def test_api_call(httpx_mock):
    httpx_mock.add_response(
        url="https://api.example.com/data",
        method="POST",
        json={"result": "success"},
        status_code=200
    )
```

**10. Что такое «фикстура с областью действия (scope)» и как она применяется в тестах БД?**

Фикстуры могут иметь разную область действия:
- function - создаётся для каждого теста (по умолчанию)
- class - один раз для класса
- module - один раз для модуля
- session - один раз за сессию

В тестах БД используется scope="function" для изоляции тестов и scope="session" для тяжёлых операций создания БД.

Пример:
```python
@pytest.fixture(scope="function")
def db_session():
    # Создаётся для каждого теста
    engine = create_engine("sqlite:///:memory:")
    session = Session(engine)
    yield session
    session.close()
```