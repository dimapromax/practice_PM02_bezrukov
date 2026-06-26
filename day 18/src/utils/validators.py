import re


def validate_card_number(card_number: str) -> bool:
    """
    Проверить номер карты (алгоритм Луна).
    
    Args:
        card_number: Номер карты (может содержать пробелы)
    
    Returns:
        True если номер валидный, иначе False
    """
    if not card_number:
        return False
    
    # Удаляем пробелы и дефисы
    card_number = card_number.replace(' ', '').replace('-', '')
    
    # Проверка, что строка состоит только из цифр
    if not card_number.isdigit():
        return False
    
    # Проверка длины (13-19 цифр)
    if len(card_number) < 13 or len(card_number) > 19:
        return False
    
    # Алгоритм Луна (исправленный)
    total = 0
    # Проходим справа налево, начиная с последней цифры
    for i in range(len(card_number) - 1, -1, -1):
        digit = int(card_number[i])
        # Каждая вторая цифра (с конца) удваивается
        if (len(card_number) - 1 - i) % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    
    return total % 10 == 0


def validate_amount(amount: float) -> bool:
    """Проверить сумму платежа"""
    return amount > 0


def validate_email(email: str) -> bool:
    """Проверить email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Проверить номер телефона"""
    pattern = r'^\+?[0-9]{10,15}$'
    return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))