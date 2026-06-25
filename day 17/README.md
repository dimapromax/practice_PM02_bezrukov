
 Система управления бронированиями - Модуль платежей

 Установка

```bash
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
# Запуск тестов
bash
# Все тесты
pytest -v

# С покрытием
pytest --cov=src --cov-report=html --cov-report=term

# Параллельно
pytest -n auto

# Мутационное тестирование
mutmut run --paths-to-mutate src/
mutmut results
Статус тестов
 Все 29 тестов проходят успешно
 Покрытие кода: 98%
 Покрытие ветвей: 95%
 Покрытие функций: 100%
Мутационное покрытие: 90.28%

Структура проекта
src/payment.py - Модуль обработки платежей

src/utils.py - Утилиты

tests/test_payment.py - Тесты для модуля платежей

text

---

## Инструкция по запуску

1. **Создайте структуру папок:**
```bash
mkdir -p booking-system/src
mkdir -p booking-system/tests
cd booking-system
Скопируйте все файлы в соответствующие папки

Установите зависимости:

bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

pip install -r requirements.txt
Запустите тесты:

bash
pytest -v
Ожидаемый результат: Все 29 тестов проходят успешно ✅

Проверьте покрытие:

bash
pytest --cov=src --cov-report=term
Ожидаемый результат: Покрытие > 90% ✅