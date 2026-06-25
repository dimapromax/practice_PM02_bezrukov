# Спецификация сервиса валидации заказов

## Версия: 1.0
## Дата: 16.06.2026
## Разработчик: Безруков Д.

## 1. Введение

Сервис валидации заказов предназначен для проверки заказов в системе доставки на соответствие бизнес-правилам. Сервис работает как "чёрный ящик" — реализация скрыта, доступен только API.

## 2. Входной формат (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["order_id", "user_id", "items", "total_amount", "created_at"],
  "properties": {
    "order_id": {
      "type": "string",
      "description": "Уникальный идентификатор заказа"
    },
    "user_id": {
      "type": "string",
      "description": "Идентификатор пользователя"
    },
    "items": {
      "type": "array",
      "minItems": 1,
      "maxItems": 50,
      "items": {
        "type": "object",
        "required": ["product_id", "quantity", "price", "category"],
        "properties": {
          "product_id": {"type": "string"},
          "quantity": {"type": "integer", "minimum": 1},
          "price": {"type": "number", "minimum": 0},
          "category": {"type": "string", "enum": ["Food", "Electronics", "Alcohol", "Clothing", "Books"]}
        }
      }
    },
    "total_amount": {
      "type": "number",
      "minimum": 0,
      "maximum": 999999.99
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Время создания заказа (UTC)"
    },
    "user_created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Время регистрации пользователя"
    },
    "user_email": {
      "type": "string",
      "format": "email"
    },
    "email_last_changed": {
      "type": "string",
      "format": "date-time",
      "description": "Время последнего изменения email"
    },
    "delivery_country": {
      "type": "string",
      "enum": ["RU", "US", "UK", "DE", "FR", "IT", "ES", "CN", "JP", "BR"]
    },
    "wallet_country": {
      "type": "string",
      "enum": ["RU", "US", "UK", "DE", "FR", "IT", "ES", "CN", "JP", "BR"]
    },
    "age_verified": {
      "type": "boolean",
      "default": false
    },
    "order_time": {
      "type": "string",
      "format": "time",
      "description": "Время оформления заказа (HH:MM:SS)"
    }
  }
}