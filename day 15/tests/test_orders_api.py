import pytest
from fastapi import status, HTTPException  # <-- ДОБАВИЛИ HTTPException
from app.dependencies import User, get_current_user
from app.services import Order
from app.main import app


# ---------------------------
# ТЕСТ 1: Доступ запрещен (403) для пользователя без роли admin
# ---------------------------
def test_get_order_forbidden_for_user(client, regular_user):
    """
    Проверяем, что обычный пользователь получает 403
    """
    # Arrange (Подготовка)
    mock_user = User(
        id=regular_user["id"],
        username=regular_user["username"],
        role=regular_user["role"]
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Act (Действие)
    response = client.get("/api/orders/1")
    
    # Assert (Проверка)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Only administrators can access orders" in response.json()["detail"]
    
    # Cleanup
    app.dependency_overrides.clear()


# ---------------------------
# ТЕСТ 2: Успешный ответ (200) для администратора
# ---------------------------
def test_get_order_success_for_admin(mocker, client, admin_user, sample_order_data):
    """
    Проверяем, что администратор получает заказ с кодом 200
    """
    # Arrange (Подготовка)
    mock_user = User(
        id=admin_user["id"],
        username=admin_user["username"],
        role=admin_user["role"]
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    mock_order = Order(
        id=sample_order_data["id"],
        total=sample_order_data["total"],
        status=sample_order_data["status"]
    )
    mocker.patch("app.main.get_order", return_value=mock_order)
    
    # Act (Действие)
    response = client.get("/api/orders/1")
    
    # Assert (Проверка)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == sample_order_data["id"]
    assert data["total"] == sample_order_data["total"]
    assert data["status"] == sample_order_data["status"]
    
    # Cleanup
    app.dependency_overrides.clear()


# ---------------------------
# ТЕСТ 3: Проверка, что заказ не найден (404)
# ---------------------------
def test_get_order_not_found(mocker, client):
    """
    Проверяем поведение при отсутствии заказа
    """
    # Arrange
    mock_user = User(id=1, username="admin", role="admin")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    mocker.patch("app.main.get_order", return_value=None)
    
    # Act
    response = client.get("/api/orders/999")
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Order 999 not found" in response.json()["detail"]
    
    # Cleanup
    app.dependency_overrides.clear()


# ---------------------------
# ТЕСТ 4: Проверка количества вызовов зависимостей
# ---------------------------
def test_get_order_calls_dependencies_correctly(mocker, client):
    """
    Проверяем, что функции-зависимости вызываются нужное количество раз
    """
    # Arrange
    mock_user = User(id=1, username="admin", role="admin")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    mock_order = Order(id=1, total=100.0)
    mock_get_order = mocker.patch("app.main.get_order", return_value=mock_order)
    
    # Act
    response = client.get("/api/orders/1")
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    mock_get_order.assert_called_once_with(1)
    
    # Cleanup
    app.dependency_overrides.clear()


# ---------------------------
# ТЕСТ 5: Проверка обработки ошибки авторизации
# ---------------------------
def test_get_order_authentication_error(client):
    """
    Проверяем, что ошибка аутентификации обрабатывается корректно
    """
    # Arrange
    def raise_auth_error():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
    
    app.dependency_overrides[get_current_user] = raise_auth_error
    
    # Act
    response = client.get("/api/orders/1")
    
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Authentication failed" in response.json()["detail"]
    
    # Cleanup
    app.dependency_overrides.clear()