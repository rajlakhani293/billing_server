from django.db import transaction
from apps.core.helpers import ResponseBuilder
from .models import Brand, Tax, Party
from apps.core.commonQuery import CommonQuery


class BrandService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                brand = CommonQuery.createRecord(Brand, data, request)
                return ResponseBuilder.success(
                    data=brand,
                    message="Brand created successfully"
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, brand_id):
        try:
            with transaction.atomic():
                brand = CommonQuery.updateRecordById(Brand, brand_id, data, request)
                if not brand:
                    raise Exception("Brand not found")
                return ResponseBuilder.success(data=brand, message="Brand updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["brand_name", True, True]]
            options = {'attributes': ['id', 'brand_name', 'status']}
            result = CommonQuery.fetchPaginatedData(Brand, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Brands retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            brands = CommonQuery.findAllRecords(Brand, {}, {'attributes': ['id', 'brand_name'], 'order': ['brand_name']}, request)
            return ResponseBuilder.success(data=brands, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = CommonQuery.softDeleteById(Brand, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Brands deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(brand_id, request):
        try:
            brand = CommonQuery.findOneRecord(Brand, brand_id, {}, request)
            if not brand or brand.get('status') == 2: raise Exception("Brand not found")
            return ResponseBuilder.success(data=brand, message="Brand retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class TaxService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                tax = CommonQuery.createRecord(Tax, data, request)
                return ResponseBuilder.success(
                    data=tax,
                    message="Tax created successfully"
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, tax_id):
        try:
            with transaction.atomic():
                tax = CommonQuery.updateRecordById(Tax, tax_id, data, request)
                if not tax:
                    raise Exception("Tax not found")
                return ResponseBuilder.success(data=tax, message="Tax updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["tax_name", True, True], ["tax_value", True, True]]
            options = {'attributes': ['id', 'tax_name', 'tax_value', 'status']}
            result = CommonQuery.fetchPaginatedData(Tax, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Taxes retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            taxes = CommonQuery.findAllRecords(Tax, {}, {'attributes': ['id', 'tax_name', 'tax_value'], 'order': ['tax_name']}, request)
            return ResponseBuilder.success(data=taxes, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = CommonQuery.softDeleteById(Tax, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Taxes deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(tax_id, request):
        try:
            tax = CommonQuery.findOneRecord(Tax, tax_id, {}, request)
            if not tax or tax.get('status') == 2: raise Exception("Tax not found")
            return ResponseBuilder.success(data=tax, message="Tax retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

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

