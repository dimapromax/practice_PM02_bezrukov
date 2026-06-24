from fastapi import FastAPI, Depends, HTTPException, status
from app.dependencies import get_current_user, User
from app.services import get_order, Order

app = FastAPI(title="Order Management System")

@app.get("/api/orders/{order_id}")
async def get_order_endpoint(
    order_id: int,
    current_user: User = Depends(get_current_user)
):
    """Получить заказ по ID (только для администраторов)"""
    # Проверка роли
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access orders"
        )
    
    # Получение заказа
    order = get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    return {
        "id": order.id,
        "total": order.total,
        "status": order.status
    }

@app.get("/api/health")
async def health_check():
    """Эндпоинт для проверки работоспособности"""
    return {"status": "ok"}