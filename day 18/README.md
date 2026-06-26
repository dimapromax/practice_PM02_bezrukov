# Booking System - Модуль payment

## Вариант 3: payment.py — Округление, комиссии, refund

### Студент: Безруков Д.
### Группа: ИС-31
### Дата: 26.06.2026

---

## Структура проекта
booking_system/
├── src/
│ ├── core/
│ │ ├── init.py
│ │ ├── domain.py # Сущности: Transaction, Refund, Payment
│ │ ├── events.py # Доменные события
│ │ └── exceptions.py # Исключения
│ ├── application/
│ │ ├── init.py
│ │ ├── services.py # PaymentService
│ │ ├── dto.py # Data Transfer Objects
│ │ └── interfaces.py # Интерфейсы (Ports)
│ ├── infrastructure/
│ │ ├── init.py
│ │ ├── repositories.py # InMemoryPaymentRepository
│ │ ├── uow.py # Unit of Work
│ │ └── external_api.py # MockPaymentGateway, NotificationService
│ ├── presentation/
│ │ ├── init.py
│ │ ├── api.py # Flask REST API
│ │ └── cli.py # CLI интерфейс
│ └── utils/
│ ├── init.py
│ ├── validators.py # Валидаторы
│ └── logger.py # Логирование
├── tests/
│ ├── init.py
│ ├── unit/
│ │ ├── init.py
│ │ ├── test_domain.py
│ │ ├── test_payment.py
│ │ └── test_validators.py
│ ├── integration/
│ │ ├── init.py
│ │ ├── test_repositories.py
│ │ └── test_api.py
│ └── fixtures/
│ ├── init.py
│ └── data_factory.py
├── requirements/
│ ├── base.txt
│ ├── dev.txt
│ └── test.txt
├── .flake8
├── mypy.ini
├── pytest.ini
├── tox.ini
├── pyproject.toml
└── README.md

text

---

## Установка и запуск

```bash
# 1. Клонирование
git clone <repository-url>
cd booking_system

# 2. Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# 3. Установка зависимостей
pip install -r requirements/test.txt
pip install -e .

# 4. Запуск API
python -m src.presentation.api

# 5. Запуск CLI
python -m src.presentation.cli --help
Тестирование
bash
# Все тесты
pytest -v

# Unit-тесты
pytest tests/unit/ -v

# Интеграционные тесты
pytest tests/integration/ -v

# С покрытием
pytest --cov=src --cov-report=html --cov-report=term

# Мутационное тестирование
mutmut run --paths-to-mutate src/
mutmut results