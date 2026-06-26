import argparse
import json
import sys
from typing import Optional

from src.application.services import PaymentService
from src.application.dto import PaymentRequestDTO, RefundRequestDTO
from src.core.exceptions import PaymentError
from src.utils.logger import setup_logging

setup_logging()


class PaymentCLI:
    """CLI для управления платежами"""
    
    def __init__(self):
        self.service = PaymentService()
    
    def process_payment(self, args):
        """Обработать платеж"""
        try:
            dto = PaymentRequestDTO(
                amount=args.amount,
                method=args.method,
                metadata={'cli': True}
            )
            result = self.service.process_payment(dto)
            
            print(json.dumps({
                'success': True,
                'transaction_id': result.transaction_id,
                'amount': result.amount,
                'commission': result.commission,
                'net_amount': result.net_amount,
                'status': result.status
            }, indent=2))
            
        except PaymentError as e:
            print(json.dumps({'success': False, 'error': str(e)}), file=sys.stderr)
            sys.exit(1)
    
    def refund_payment(self, args):
        """Выполнить возврат"""
        try:
            dto = RefundRequestDTO(
                transaction_id=args.transaction_id,
                original_amount=args.amount,
                days_before=args.days_before
            )
            result = self.service.refund_payment(dto)
            
            if result.success:
                print(json.dumps({
                    'success': True,
                    'refund_amount': result.refund_amount,
                    'fee': result.fee
                }, indent=2))
            else:
                print(json.dumps({'success': False, 'error': result.error}), file=sys.stderr)
                sys.exit(1)
                
        except PaymentError as e:
            print(json.dumps({'success': False, 'error': str(e)}), file=sys.stderr)
            sys.exit(1)
    
    def get_transaction(self, args):
        """Получить информацию о транзакции"""
        transaction = self.service.get_transaction(args.transaction_id)
        
        if transaction:
            print(json.dumps({
                'success': True,
                'data': {
                    'transaction_id': transaction.id,
                    'amount': transaction.amount,
                    'method': transaction.method.value,
                    'commission': transaction.commission,
                    'net_amount': transaction.net_amount,
                    'status': transaction.status.value,
                    'created_at': transaction.created_at.isoformat()
                }
            }, indent=2))
        else:
            print(json.dumps({'success': False, 'error': 'Transaction not found'}), file=sys.stderr)
            sys.exit(1)
    
    def validate_card(self, args):
        """Валидация карты"""
        is_valid = self.service.validate_card_number(args.card_number)
        print(json.dumps({
            'success': True,
            'card': args.card_number[:4] + '****' + args.card_number[-4:] if len(args.card_number) >= 8 else '****',
            'is_valid': is_valid
        }, indent=2))


def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(
        description='Payment System CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Команда: process-payment
    payment_parser = subparsers.add_parser('process-payment', help='Process payment')
    payment_parser.add_argument('--amount', type=float, required=True, help='Payment amount')
    payment_parser.add_argument('--method', type=str, default='card', help='Payment method')
    
    # Команда: refund
    refund_parser = subparsers.add_parser('refund', help='Process refund')
    refund_parser.add_argument('--transaction-id', type=str, required=True, help='Transaction ID')
    refund_parser.add_argument('--amount', type=float, required=True, help='Original amount')
    refund_parser.add_argument('--days-before', type=int, default=7, help='Days before check-in')
    
    # Команда: get-transaction
    get_parser = subparsers.add_parser('get-transaction', help='Get transaction info')
    get_parser.add_argument('--transaction-id', type=str, required=True, help='Transaction ID')
    
    # Команда: validate-card
    validate_parser = subparsers.add_parser('validate-card', help='Validate card number')
    validate_parser.add_argument('--card-number', type=str, required=True, help='Card number')
    
    args = parser.parse_args()
    
    cli = PaymentCLI()
    
    if args.command == 'process-payment':
        cli.process_payment(args)
    elif args.command == 'refund':
        cli.refund_payment(args)
    elif args.command == 'get-transaction':
        cli.get_transaction(args)
    elif args.command == 'validate-card':
        cli.validate_card(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()