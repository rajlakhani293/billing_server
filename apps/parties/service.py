from django.db import transaction
from apps.core.helpers import ResponseBuilder, validate_request
from .models import Party
from apps.core.commonQuery import CommonQuery, common_query


class PartyService:
    
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                # Define required fields with display names
                required_fields = {
                    'name': 'Party Name',
                    'party_type': 'Party Type',
                    'customer_category': 'Customer Category'
                }
                
                # Define unique checks
                unique_checks = {
                    'model': Party,
                    'fields': ['phone_number', 'email']
                }
                
                # Validate request
                errors = validate_request(data, required_fields, unique_checks, request)
                if errors:
                    raise Exception(f"Validation failed: {errors}")
                
                # Create party using CommonQuery within transaction
                party = CommonQuery.createRecord(Party, data, request)
                
                # Serialize party object
                serialized_party = CommonQuery.serializeModelInstance(party)
                
                # Transaction commits automatically when context manager exits successfully
                return ResponseBuilder.success(
                    data=serialized_party,
                    message="Party created successfully"
                )
                
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
    
    @staticmethod
    def update(data, request, party_id):
        try:
            with transaction.atomic():
                # Define required fields with display names
                required_fields = {
                    'name': 'Party Name',
                    'party_type': 'Party Type',
                    'customer_category': 'Customer Category'
                }
                
                # Define unique checks with exclude_id for update
                unique_checks = {
                    'model': Party,
                    'fields': ['phone_number', 'email'],
                    'exclude_id': party_id
                }
                
                # Validate request
                errors = validate_request(data, required_fields, unique_checks, request)
                if errors:
                    # Transaction automatically rolls back when exception is raised
                    raise Exception(f"Validation failed: {errors}")
                
                # Update party using CommonQuery within transaction
                party = CommonQuery.updateRecordById(Party, party_id, data, request)
                
                if not party:
                    raise Exception("Party not found")
                
                # Serialize party object
                serialized_party = CommonQuery.serializeModelInstance(party)
                
                # Transaction commits automatically when context manager exits successfully
                return ResponseBuilder.success(
                    data=serialized_party,
                    message="Party updated successfully"
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
                ["name", True, True],
                ["wallet_balance", True, True],
                ["party_type", True, True],
                ["customer_category", True, True],
            ]
            
            # Options for related data
            options = {
                'select_related': ['city', 'state', 'country', 'shop'],
                'sumField': ['wallet_balance']
            }
            
            # Custom related fields configuration
            custom_related_fields = {
                'city': ['id', 'name'],
                'state': ['id', 'name'],
                'country': ['id', 'name'],
                'shop': ['id', 'shop_name']
            }
            
            # Fetch paginated data using CommonQuery with custom serialization
            result = CommonQuery.fetchPaginatedData(
                Party, data, fieldConfig, options, request, custom_related_fields=custom_related_fields
            )
            
            return ResponseBuilder.success(
                data=result,
                message="Parties retrieved successfully"
            )
            
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
    
    @staticmethod
    def getById(party_id, request):
        try:
            party = CommonQuery.findOneRecord(
                Party, 
                party_id, 
                {
                    'select_related': ['city', 'state', 'country', 'shop'],
                    'custom_related_fields': {
                        'city': ['id', 'name'],
                        'state': ['id', 'name'],
                        'country': ['id', 'name'],
                        'shop': ['id', 'shop_name']
                    }
                },
                request
            )
            
            if not party:
                raise Exception("Party not found")
            
            return ResponseBuilder.success(
                data=party,
                message="Party retrieved successfully"
            )
            
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
    
    @staticmethod
    def delete(party_id, request):
        try:
            with transaction.atomic():
                # Soft delete using transaction
                count = CommonQuery.softDeleteById(Party, party_id, request)
                
                if count == 0:
                    raise Exception("Party not found")
                
                # Transaction commits automatically when context manager exits successfully
                return ResponseBuilder.success(
                    message="Party deleted successfully"
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
                party_id = data.get('id')
                status = data.get('status')
                
                if not party_id or status is None:
                    raise Exception("Party ID and status are required")
                
                # Update status using transaction
                party = CommonQuery.updateRecordById(Party, party_id, {'status': status}, request)
                
                if not party:
                    raise Exception("Party not found")
                
                # Serialize party object
                serialized_party = CommonQuery.serializeModelInstance(party)
                
                # Transaction commits automatically when context manager exits successfully
                return ResponseBuilder.success(
                    data=serialized_party,
                    message="Party status updated successfully"
                )
                
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
    
    @staticmethod
    def dropdownList(request):
        try:         
            parties = CommonQuery.findAllRecords(
                Party, 
                {'status': 0},
                {'attributes': ['id', 'name', 'party_type', 'phone_number', 'email'], 'order': ['name']},
                request
            )
            
            return ResponseBuilder.success(
                data=parties,
                message="Dropdown list retrieved successfully"
            )
            
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )
