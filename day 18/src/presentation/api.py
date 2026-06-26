import json
from typing import Optional

from flask import Flask, request, jsonify, abort

from src.application.services import PaymentService
from src.application.dto import (
    PaymentRequestDTO,
    RefundRequestDTO,
    CommissionRequestDTO
)
from src.core.exceptions import (
    PaymentError,
    InvalidAmountError,
    TransactionNotFoundError,
    PaymentMethodNotSupportedError
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Создание Flask приложения
app = Flask(__name__)

# Инициализация сервисов
payment_service = PaymentService()


@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({'status': 'ok', 'service': 'payment'})


@app.route('/api/payments', methods=['POST'])
def process_payment():
    """Обработать платеж"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Создание DTO
        dto = PaymentRequestDTO(
            amount=data.get('amount', 0.0),
            method=data.get('method', 'card'),
            metadata=data.get('metadata')
        )
        
        # Обработка платежа
        result = payment_service.process_payment(dto)
        
        return jsonify({
            'success': True,
            'data': {
                'transaction_id': result.transaction_id,
                'amount': result.amount,
                'commission': result.commission,
                'net_amount': result.net_amount,
                'status': result.status
            }
        }), 200
        
    except InvalidAmountError as e:
        return jsonify({'error': str(e)}), 400
    except PaymentMethodNotSupportedError as e:
        return jsonify({'error': str(e)}), 400
    except PaymentError as e:
        logger.error(f"Payment error: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/payments/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id: str):
    """Получить информацию о транзакции"""
    try:
        transaction = payment_service.get_transaction(transaction_id)
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'transaction_id': transaction.id,
                'amount': transaction.amount,
                'method': transaction.method.value,
                'commission': transaction.commission,
                'net_amount': transaction.net_amount,
                'status': transaction.status.value,
                'created_at': transaction.created_at.isoformat(),
                'updated_at': transaction.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting transaction: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/payments/refund', methods=['POST'])
def process_refund():
    """Обработать возврат"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        dto = RefundRequestDTO(
            transaction_id=data.get('transaction_id', ''),
            original_amount=data.get('original_amount', 0.0),
            days_before=data.get('days_before', 0)
        )
        
        result = payment_service.refund_payment(dto)
        
        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'refund_amount': result.refund_amount,
                'fee': result.fee
            }
        }), 200
        
    except InvalidAmountError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/commission', methods=['POST'])
def calculate_commission():
    """Рассчитать комиссию"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        dto = CommissionRequestDTO(
            amount=data.get('amount', 0.0),
            commission_rate=data.get('commission_rate', 0.025)
        )
        
        result = payment_service.calculate_commission(dto.amount, dto.commission_rate)
        
        return jsonify({
            'success': True,
            'data': {
                'commission': result.commission,
                'amount': result.amount,
                'rate': result.rate
            }
        }), 200
        
    except InvalidAmountError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error calculating commission: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate-card', methods=['POST'])
def validate_card():
    """Валидация номера карты"""
    try:
        data = request.get_json()
        card_number = data.get('card_number', '')
        
        is_valid = payment_service.validate_card_number(card_number)
        
        return jsonify({
            'success': True,
            'data': {
                'card_number': card_number[:4] + '****' + card_number[-4:] if len(card_number) >= 8 else '****',
                'is_valid': is_valid
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating card: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tax', methods=['POST'])
def calculate_tax():
    """Рассчитать сумму с налогом"""
    try:
        data = request.get_json()
        amount = data.get('amount', 0.0)
        tax_rate = data.get('tax_rate', 0.20)
        
        result = payment_service.calculate_total_with_tax(amount, tax_rate)
        
        return jsonify({
            'success': True,
            'data': {
                'amount': amount,
                'tax_rate': tax_rate,
                'total': result
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating tax: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)