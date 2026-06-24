class User:
    def __init__(self, id: int, username: str, role: str):
        self.id = id
        self.username = username
        self.role = role


def get_current_user() -> User:
    """Реальная реализация будет использовать JWT/сессии"""
    # В тестах мы будем мокать эту функцию
    return User(id=1, username="admin", role="admin")