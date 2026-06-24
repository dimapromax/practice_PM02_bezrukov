import logging
import sys
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Кастомный форматтер для структурированного логирования"""
    
    def format(self, record):
        # Добавляем временную метку
        record.timestamp = datetime.now().isoformat()
        
        # Форматируем сообщение в JSON-подобный вид
        log_entry = {
            "timestamp": record.timestamp,
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage()
        }
        
        # Добавляем исключение, если есть
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return str(log_entry)

def setup_logging(level=logging.INFO):
    """Настройка логирования"""
    # Создаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Очищаем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(console_handler)
    
    # Создаем обработчик для файла
    file_handler = logging.FileHandler('clinic.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(file_handler)
    
    logger = logging.getLogger(__name__)
    logger.info("Логирование настроено")
    
    return root_logger