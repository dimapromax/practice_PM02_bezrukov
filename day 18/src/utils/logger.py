import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO") -> None:
    """Настройка логирования"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('booking_system.log')
        ]
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Получить логгер"""
    if name is None:
        name = __name__
    return logging.getLogger(name)