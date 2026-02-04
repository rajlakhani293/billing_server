from django.db import transaction
from django.conf import settings
from apps.core.helpers import ResponseBuilder, generate_sequential_code
from .models import Item, ItemCategory, ItemUnit
from apps.core.commonQuery import CommonQuery, uploadFile

class ItemCategoryService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                category = CommonQuery.createRecord(ItemCategory, data, request)
                return ResponseBuilder.success(
                    data=category,
                    message="Category created successfully"
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, category_id):
        try:
            with transaction.atomic():
                category = CommonQuery.updateRecordById(ItemCategory, category_id, data, request)
                if not category:
                    raise Exception("Category not found")
                return ResponseBuilder.success(data=category, message="Category updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["name", True, True]]
            options = {'attributes': ['id', 'name', 'description', 'status']}
            result = CommonQuery.fetchPaginatedData(ItemCategory, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Categories retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            categories = CommonQuery.findAllRecords(ItemCategory, {'status': 0}, {'attributes': ['id', 'name'], 'order': ['name']}, request)
            return ResponseBuilder.success(data=categories, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = CommonQuery.softDeleteById(ItemCategory, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Categories deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(category_id, request):
        try:
            category = CommonQuery.findOneRecord(ItemCategory, category_id, {}, request)
            if not category or category.get('status') == 2: raise Exception("Category not found")
            return ResponseBuilder.success(data=category, message="Category retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class ItemUnitService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                unit = CommonQuery.createRecord(ItemUnit, data, request)
                return ResponseBuilder.success(data=unit, message="Unit created successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, unit_id):
        try:
            with transaction.atomic():
                unit = CommonQuery.updateRecordById(ItemUnit, unit_id, data, request)
                if not unit:
                    raise Exception("Unit not found")
                return ResponseBuilder.success(data=unit, message="Unit updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["name", True, True], ["short_name", True, True]]
            options = {'attributes': ['id', 'name', 'short_name', 'status']}
            result = CommonQuery.fetchPaginatedData(ItemUnit, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Units retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            units = CommonQuery.findAllRecords(ItemUnit, {}, {'attributes': ['id', 'name', 'short_name'], 'order': ['name']}, request)
            return ResponseBuilder.success(data=units, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = CommonQuery.softDeleteById(ItemUnit, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Units deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
    
    @staticmethod
    def getById(unit_id, request):
        try:
            unit = CommonQuery.findOneRecord(ItemUnit, unit_id, {}, request)
            if not unit or unit.get('status') == 2: raise Exception("Unit not found")
            return ResponseBuilder.success(data=unit, message="Unit retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class ItemService:
    
    @staticmethod
    def create(request, payload: dict, image_file=None):
        try:
            with transaction.atomic():

                if image_file:
                    saved_files = uploadFile(image_file, subfolder="items")
                    payload['item_image'] = saved_files.get('file')
                
                payload['item_code'] = generate_sequential_code(Item, 'item_code', 'IT')

                item = CommonQuery.createRecord(Item, payload, request)

                return ResponseBuilder.success(
                    message="Item created successfully",
                    data=item
                )
        except Exception as e:
            return ResponseBuilder.error(str(e))

    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = CommonQuery.softDeleteById(Item, data.get('ids'), request)
                
                if count == 0:
                    raise Exception("No records found")
                
                return ResponseBuilder.success(
                    message="Items deleted successfully"
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
    def dropdownList(request):
        try:         
            items = CommonQuery.findAllRecords(
                Item, 
                {},
                {'attributes': ['id', 'item_name', 'item_code', 'current_stock', 'selling_price', 'item_image'], 'order': ['item_name']},
                request
            )
            
            # Post-process to add full image URL
            for item in items:
                if item.get('item_image'):
                    item['item_image'] = request.build_absolute_uri(settings.MEDIA_URL + str(item['item_image']))
                else:
                    item['item_image'] = None
            
            return ResponseBuilder.success(
                data=items,
                message="Dropdown list retrieved successfully"
            )
            
        except Exception as e:
            return ResponseBuilder.error(
                message=str(e),
                status_code=400
            )

    @staticmethod
    def getById(item_id, request):
        try:
            item = CommonQuery.findOneRecord(Item, item_id, {}, request)
            if not item or item.get('status') == 2: raise Exception("Item not found")
            return ResponseBuilder.success(data=item, message="Item retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)