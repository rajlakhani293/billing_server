from django.db import transaction
from apps.core.helpers import ResponseBuilder
from apps.core.commonQuery import CommonQuery
from .models import Party

class PartyService:

    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                CommonQuery.createRecord(Party, data, request)
                return ResponseBuilder.success(message="Party created successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, record_id):
        try:
            with transaction.atomic():
                CommonQuery.updateRecordById(Party, record_id, data, request)
                return ResponseBuilder.success(message="Party updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                CommonQuery.softDeleteById(Party, data.get('ids'), request)
                return ResponseBuilder.success(message="Parties deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            # Field configuration: [field_name, is_searchable, is_sortable]
            fieldConfig = [
                ["name", True, True],
                ["phone_number", True, True],
                ["email", True, True],
                ["party_type", False, True],
            ]
            
            result = CommonQuery.fetchPaginatedData(Party, data, fieldConfig, None, request)
            return ResponseBuilder.success(data=result, message="Parties retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(party_id, request):
        try:
            party = CommonQuery.findOneRecord(Party, party_id, {}, request)
            if not party or party.get('status') == 2: raise Exception("Party not found")
            return ResponseBuilder.success(data=party, message="Party retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            # Dropdown usually needs id and name
            parties = CommonQuery.findAllRecords(
                Party, 
                {}, 
                {'attributes': ['id', 'name', 'party_type', 'phone_number'], 'order': ['name']}, 
                request
            )
            return ResponseBuilder.success(data=parties, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
