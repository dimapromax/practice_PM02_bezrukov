class PaymentError(Exception):
    """Базовое исключение для ошибок платежей"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class InvalidAmountError(PaymentError):
    """Некорректная сумма платежа"""
    pass


class InsufficientFundsError(PaymentError):
    """Недостаточно средств"""
    pass


class TransactionNotFoundError(PaymentError):
    """Транзакция не найдена"""
    pass


class PaymentMethodNotSupportedError(PaymentError):
    """Неподдерживаемый метод оплаты"""
    pass


class RefundError(PaymentError):
    """Ошибка возврата средств"""
    pass


class CardValidationError(PaymentError):
    """Ошибка валидации карты"""
    pass