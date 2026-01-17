from django.db import transaction
from apps.core.helpers import ResponseBuilder, handle_response
from .models import Party
from apps.core.commonQuery import CommonQuery


class PartyService:
    
    # @staticmethod
    # def create(data, request):
    #     try:
    #         with transaction.atomic():
    #             # Validate party data
    #             if data.get('party_type') == 1 and not data.get('customer_category'):
    #                 return ResponseBuilder.error('Customer category is required for customers.')
                
    #             if data.get('wallet_balance') and data.get('wallet_balance') < 0:
    #                 return ResponseBuilder.error('Wallet balance cannot be negative.')
                
    #             # Create party using common query
    #             party = CommonQuery.createRecord(Party, data, request)
                
    #             return ResponseBuilder.success(
    #                 'Party created successfully',
    #                 {
    #                     'party': party
    #                 }
    #             )
    #     except Exception as e:
    #         return ResponseBuilder.error(str(e))


    @staticmethod
    def create(request, payload):
        result = PartyService.create(payload.dict(), request)
        return handle_response(result)
    
    @staticmethod
    def update(data, request):
        try:
            party_id = data.get('id')
            if not party_id:
                return ResponseBuilder.error('Party ID is required')
            
            # Get existing party
            existing_party = CommonQuery.findOneRecord(Party, {'id': party_id}, request=request)
            if not existing_party:
                return ResponseBuilder.error('Party not found')
            
            # Validate update data
            update_data = {k: v for k, v in data.items() if k != 'id' and v is not None}
            
            if 'party_type' in update_data or 'customer_category' in update_data:
                party_type = update_data.get('party_type', existing_party.party_type)
                customer_category = update_data.get('customer_category', existing_party.customer_category)
                
                if party_type == 1 and not customer_category:
                    return ResponseBuilder.error('Customer category is required for customers.')
            
            if 'wallet_balance' in update_data and update_data['wallet_balance'] < 0:
                return ResponseBuilder.error('Wallet balance cannot be negative.')
            
            # Update party using common query
            updated_party = CommonQuery.updateRecordById(Party, party_id, update_data, request)
            
            return ResponseBuilder.success(
                'Party updated successfully',
                {
                    'party': updated_party
                }
            )
        except Exception as e:
            return ResponseBuilder.error(str(e))
    
    @staticmethod
    def getAll(request_body, request):
        try:
            # Field configuration for search
            field_config = [
                ('name', True),
                ('phone_number', True),
                ('email', True),
                ('address', True)
            ]
            
            # Options for pagination
            options = {
                'sumField': ['wallet_balance']
            }
            
            # Get paginated data using common query
            result = CommonQuery.fetchPaginatedData(
                Party, 
                request_body, 
                field_config, 
                options, 
                request
            )
            
            # Serialize related objects
            serialized_items = []
            for item in result['items']:
                item_data = CommonQuery.serializeModelInstance(item)
                
                # Add related objects
                if item.city:
                    item_data['city'] = {
                        'id': item.city.id,
                        'name': item.city.name
                    }
                if item.state:
                    item_data['state'] = {
                        'id': item.state.id,
                        'name': item.state.name
                    }
                if item.country:
                    item_data['country'] = {
                        'id': item.country.id,
                        'name': item.country.name
                    }
                
                serialized_items.append(item_data)
            
            result['items'] = serialized_items
            
            return ResponseBuilder.success(
                'Parties retrieved successfully',
                {
                    'parties': result
                }
            )
        except Exception as e:
            return ResponseBuilder.error(str(e))
    
    @staticmethod
    def getById(party_id, request):
        try:
            # Get party with related objects
            options = {
                'select_related': ['city', 'state', 'country']
            }
            
            party = CommonQuery.findOneRecord(Party, {'id': party_id}, options, request)
            
            if not party:
                return ResponseBuilder.error('Party not found')
            
            # Serialize party data
            party_data = CommonQuery.serializeModelInstance(party)
            
            # Add related objects
            if party.city:
                party_data['city'] = {
                    'id': party.city.id,
                    'name': party.city.name
                }
            if party.state:
                party_data['state'] = {
                    'id': party.state.id,
                    'name': party.state.name
                }
            if party.country:
                party_data['country'] = {
                    'id': party.country.id,
                    'name': party.country.name
                }
            
            return ResponseBuilder.success(
                'Party retrieved successfully',
                party_data
            )
        except Exception as e:
            return ResponseBuilder.error(f'Error retrieving party: {str(e)}')
    
    @staticmethod
    def delete(party_id, request):
        try:
            # Soft delete party using common query
            deleted_count = CommonQuery.softDeleteById(Party, party_id, request)
            
            if deleted_count == 0:
                return ResponseBuilder.error('Party not found')
            
            return ResponseBuilder.success('Party deleted successfully')
        except Exception as e:
            return ResponseBuilder.error(f'Error deleting party: {str(e)}')
    
    @staticmethod
    def updateStatus(data, request):
        try:
            party_id = data.get('id')
            status = data.get('status')
            
            if not party_id or status is None:
                return ResponseBuilder.error('Party ID and status are required')
            
            # Check if party exists
            existing_party = CommonQuery.findOneRecord(Party, {'id': party_id}, request=request)
            if not existing_party:
                return ResponseBuilder.error('Party not found')
            
            # Update status using common query
            updated_party = CommonQuery.updateRecordById(Party, party_id, {'status': status}, request)
            
            return ResponseBuilder.success(
                'Party status updated successfully',
                updated_party
            )
        except Exception as e:
            return ResponseBuilder.error(f'Error updating party status: {str(e)}')
    
    @staticmethod
    def dropdownList(request_body, request):
        try:
            # Build filters
            filters = request_body.get('filter', {})
            
            # Add status filter (only active parties)
            filters['status'] = 0
            
            # Add party type filter if provided
            if request_body.get('party_type'):
                filters['party_type'] = request_body['party_type']
            
            # Get parties using common query
            options = {
                'order': ['name']
            }
            
            parties = CommonQuery.findAllRecords(Party, filters, options, request)
            
            # Serialize dropdown data
            dropdown_data = []
            for party in parties:
                party_data = {
                    'id': party.id,
                    'name': party.name,
                    'party_type': party.party_type,
                    'phone_number': party.phone_number,
                    'email': party.email
                }
                dropdown_data.append(party_data)
            
            return ResponseBuilder.success(
                'Party dropdown list retrieved successfully',
                dropdown_data
            )
        except Exception as e:
            return ResponseBuilder.error(f'Error retrieving party dropdown list: {str(e)}')
