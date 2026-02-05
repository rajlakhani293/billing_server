from django.db import transaction
from apps.core.helpers import ResponseBuilder, generate_sequential_code
from .models import Sales, SalesTransaction
from apps.core.commonQuery import CommonQuery, get_auth_context

class SalesService:
    
    @staticmethod
    def create(request, payload: dict):
        try:
            with transaction.atomic():
                # Extract transactions data
                transactions_data = payload.pop('transactions', [])
                
                # Generate Sales Code
                payload['sales_code'] = generate_sequential_code(Sales, 'sales_code', 'SL')
                
                # Create Sales Record
                sales = CommonQuery.createRecord(Sales, payload, request)
                
                # Create Sales Transactions
                for trans_data in transactions_data:
                    trans_data['sales_id'] = sales['id']
                    # Ensure status is active by default if not provided
                    if 'status' not in trans_data:
                        trans_data['status'] = 0
                    CommonQuery.createRecord(SalesTransaction, trans_data, request)
                
                return ResponseBuilder.success(
                    message="Sales created successfully",
                    data=sales
                )
        except Exception as e:
            return ResponseBuilder.error(str(e))

    @staticmethod
    def delete(data, request):
        try:
            ids = data.get('ids')
            with transaction.atomic():
                count = CommonQuery.softDeleteById(Sales, ids, request)
                
                if count == 0:
                    raise Exception("No records found")

                transactions = CommonQuery.findAllRecords(
                    SalesTransaction, 
                    {'sales': ids}, 
                    {'attributes': ['id']}, 
                    request
                )
                
                transaction_ids = [t['id'] for t in transactions]
                
                if transaction_ids:
                    CommonQuery.softDeleteById(SalesTransaction, transaction_ids, request)
                
                return ResponseBuilder.success(
                    message="Sales deleted successfully"
                )
                
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )

    @staticmethod
    def getAll(data, request):
        try:
            # Field configuration: [field_name, is_searchable, is_sortable]
            fieldConfig = [
                ["sales_code", True, True],
                ["party__name", True, True],
                ["total_amount", True, True],
                ["payment_mode", True, True],
                ["sales_date", True, True],
            ]
            
            options = {
                'attributes': [
                    'id', 'sales_code', 'party__name', 'sales_date', 
                    'total_amount', 'paid_amount', 'payment_mode', 'status'
                ],
            }
            
            result = CommonQuery.fetchPaginatedData(
                Sales, data, fieldConfig, options, request
            )
            
            return ResponseBuilder.success(
                data=result,
                message="Sales retrieved successfully"
            )
            
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )

    @staticmethod
    def getById(sales_id, request):
        try:
            # Fetch the main sales record
            sales = CommonQuery.findOneRecord(Sales, sales_id, {}, request)
            if not sales or sales.get('status') == 2: 
                raise Exception("Sales record not found")
            
            # Fetch associated transactions
            # We can use CommonQuery to find all transactions for this sale
            transactions = CommonQuery.findAllRecords(
                SalesTransaction, 
                {'sales_id': sales_id, 'status': 0}, 
                {'attributes': ['id', 'item__item_name', 'item_quantity', 'item_rate', 'total_amount', 'item_description', 'discount_percentage', 'discount_amount', 'tax_amount']}, 
                request
            )
            
            sales['transactions'] = transactions
            
            return ResponseBuilder.success(data=sales, message="Sales retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
