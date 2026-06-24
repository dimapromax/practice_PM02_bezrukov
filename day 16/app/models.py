from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, Float, ForeignKey, 
    CheckConstraint, Numeric
)
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy.sql import func

Base = declarative_base()


class Order(Base):
    """Модель заказа."""
    
    __tablename__ = 'orders'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default='PENDING',
        server_default='PENDING'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        server_default=func.now()
    )
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(200), nullable=False)
    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False, 
        default=0.0
    )
    
    # Отношение к позициям заказа
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", 
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Ограничения
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PAID', 'SHIPPED', 'CANCELLED')",
            name='valid_status'
        ),
        CheckConstraint("total_amount >= 0", name='positive_total_amount'),
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, status='{self.status}', customer='{self.customer_name}')>"


class OrderItem(Base):
    """Модель позиции заказа."""
    
    __tablename__ = 'order_items'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('orders.id', ondelete='CASCADE'), 
        nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Отношение к заказу
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    
    # Ограничения
    __table_args__ = (
        CheckConstraint("quantity > 0", name='positive_quantity'),
        CheckConstraint("price >= 0", name='non_negative_price'),
    )
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, product='{self.product_name}', quantity={self.quantity})>"