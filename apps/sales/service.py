from django.db import transaction
from apps.core.helpers import ResponseBuilder, validate_request, generate_sequential_code
from .models import Sales, SalesTransaction
from apps.core.commonQuery import CommonQuery
import datetime
import random


class SalesService:
    
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                # Extract transactions
                transactions_data = data.pop('transactions', [])
                
                # Generate sales_code
                data['sales_code'] = generate_sequential_code(Sales, 'sales_code', 'SL')
                
                # Validate uniqueness of sales_code loop if needed? 
                # For now assume collision low.
                
                # Create Sales Record
                sales = CommonQuery.createRecord(Sales, data, request)
                
                # Create Transactions
                for trans_data in transactions_data:
                    trans_data['sales_id'] = sales.id
                    # Ensure item_id is passed correctly to FK
                    if 'item_id' in trans_data:
                        trans_data['item_id'] = trans_data.pop('item_id')
                    
                    CommonQuery.createRecord(SalesTransaction, trans_data, request)
                
                # Serialize response ? Or just return ID
                return ResponseBuilder.success(
                    data={'id': sales.id, 'sales_code': sales.sales_code},
                    message="Sales created successfully"
                )
                
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )

    @staticmethod
    def revoke(data, request):
        try:
            with transaction.atomic():
                ids = data.get('ids')
                if not isinstance(ids, list) or not ids:
                    raise Exception("Select at least one record")
                
                sales_revoked = CommonQuery.softDeleteById(Sales, ids, request)
                
                if sales_revoked == 0:
                     raise Exception("Sales not found or already deleted")
                
                # Soft delete related transactions
                SalesTransaction.objects.filter(sales_id__in=ids).update(status=2)

                return ResponseBuilder.success(
                    message="Sales revoked successfully"
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
                ["party__name", True, True], # Search by party name
            ]
            
            # Options for related data
            options = {
                'select_related': ['party', 'shop'],
                'sumField': ['total_amount']
            }
            
            custom_related_fields = {
                'party': ['id', 'name'],
                'shop': ['id', 'shop_name']
            }
            
            result = CommonQuery.fetchPaginatedData(
                Sales, data, fieldConfig, options, request, custom_related_fields=custom_related_fields
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
