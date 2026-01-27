from django.db import transaction
from apps.core.helpers import ResponseBuilder, validate_request
from .models import Item
from apps.core.commonQuery import CommonQuery

class ItemService:
    
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                # Define required fields with display names
                required_fields = {
                    'item_code': 'Item Code',
                    'item_name': 'Item Name',
                    'primary_unit': 'Primary Unit',
                }
                
                # Define unique checks
                unique_checks = {
                    'model': Item,
                    'fields': ['item_code']
                }
                
                # Validate request
                errors = validate_request(data, required_fields, unique_checks, request)
                if errors:
                    raise Exception(f"Validation failed: {errors}")
                
                # Create item using CommonQuery within transaction
                item = CommonQuery.createRecord(Item, data, request)
                
                # Serialize item object
                serialized_item = CommonQuery.serializeModelInstance(item)
                
                return ResponseBuilder.success(
                    data=serialized_item,
                    message="Item created successfully"
                )
                
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
    
    @staticmethod
    def update(data, request, item_id):
        try:
            with transaction.atomic():    
                # Define required fields with display names
                required_fields = {
                    'item_code': 'Item Code',
                    'item_name': 'Item Name',
                    'primary_unit': 'Primary Unit',
                }
                
                # Define unique checks
                unique_checks = {
                    'model': Item,
                    'fields': ['item_code'],
                    'exclude_id': item_id
                }
                
                # Validate request
                errors = validate_request(data, required_fields, unique_checks, request)
                if errors:
                    raise Exception(f"Validation failed: {errors}")
                
                # Update item using CommonQuery within transaction
                item = CommonQuery.updateRecordById(Item, item_id, data, request)
                
                if not item:
                    raise Exception("Item not found")
                
                # Serialize item object
                serialized_item = CommonQuery.serializeModelInstance(item)
                
                return ResponseBuilder.success(
                    data=serialized_item,
                    message="Item updated successfully"
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
                ["item_name", True, True],
                ["item_code", True, True],
                ["brand", True, True],
                ["selling_price", True, True],
                ["current_stock", True, True],
            ]
            
            options = {
                'attributes': ['id', 'item_name', 'item_code', 'current_stock', 'selling_price', 'status', 'brand'],
            }
            
            result = CommonQuery.fetchPaginatedData(
                Item, data, fieldConfig, options, request
            )
            
            return ResponseBuilder.success(
                data=result,
                message="Items retrieved successfully"
            )
            
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )

    
    @staticmethod
    def getById(item_id, request):
        try:
            item = CommonQuery.findOneRecord(
                Item, 
                item_id, 
                {},
                request
            )
            
            if not item or item.get('status') == 2:
                raise Exception("Item not found")
            
            return ResponseBuilder.success(
                data=item,
                message="Item retrieved successfully"
            )
            
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
    
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                ids = data.get('ids')
                if not isinstance(ids, list) or not ids:
                    raise Exception("Select at least one record")
                
                # Soft delete using transaction
                count = CommonQuery.softDeleteById(Item, ids, request)
                
                if count == 0:
                    raise Exception("Already deleted")
                
                return ResponseBuilder.success(
                    message="Items deleted successfully"
                )
                
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
    
    @staticmethod
    def updateStatus(data, request):
        try:
            with transaction.atomic():
                ids = data.get('ids')
                status = data.get('status')
                
                if not isinstance(ids, list) or not ids:
                    raise Exception("Select at least one record")
                
                if status not in [0, 1]:
                    raise Exception("Invalid status")
                
                # Update status using transaction
                updated_record = CommonQuery.updateRecordById(Item, ids, {'status': status}, request)
                
                if not updated_record:
                    raise Exception("Records not found")
                
                return ResponseBuilder.success(
                    message="Items status updated successfully"
                )
                
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
    
    @staticmethod
    def dropdownList(request):
        try:         
            items = CommonQuery.findAllRecords(
                Item, 
                {'status': 0},
                {'attributes': ['id', 'item_name', 'item_code', 'current_stock', 'selling_price'], 'order': ['item_name']},
                request
            )
            
            return ResponseBuilder.success(
                data=items,
                message="Dropdown list retrieved successfully"
            )
            
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
