import pytest 
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import random 
from fake_validator import FakeValidator, create_validator

pytest test_validate_order.py -v

# Запуск только параметризованных тестов
pytest test_validate_order.py -v -k "test_validate_order_decision_table"

# Запуск с отладкой
pytest test_validate_order.py -v --tb=short