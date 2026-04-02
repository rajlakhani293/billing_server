from django.db import transaction
from django.conf import settings
from apps.core.helpers import ResponseBuilder, generateSequentialCode, uploadFile
from .models import Item, ItemCategory, ItemUnit, StockLedger
from apps.core.tenantQuery import TenantQuery
from apps.core.constants import ITEM_IMG_FOLDER, ITEM_CODE_PREFIX
import json
from decimal import Decimal, InvalidOperation

class ItemCategoryService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                category = TenantQuery.createRecord(ItemCategory, data, request)
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
                category = TenantQuery.updateRecordById(ItemCategory, category_id, data, request)
                if not category:
                    raise Exception("Category not found")
                return ResponseBuilder.success(data=category, message="Category updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["category_name", True, True]]
            options = {'attributes': ['id', 'category_name', 'description', 'status']}
            result = TenantQuery.fetchPaginatedData(ItemCategory, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Categories retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            categories_with_counts = TenantQuery.findAllRecords(
                ItemCategory, 
                {}, 
                {
                    'attributes': ['id', 'category_name'], 
                    'order': ['category_name']
                }, 
                request
            )
            
            for category in categories_with_counts:
                item_count = TenantQuery.countRecords(
                    Item,
                    {'category': category['id'], 'status': 0},
                    request
                )
                category['item_count'] = item_count
            
            return ResponseBuilder.success(data=categories_with_counts, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = TenantQuery.softDeleteById(ItemCategory, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Categories deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(category_id, request):
        try:
            category = TenantQuery.findOneRecord(ItemCategory, category_id, {}, request)
            if not category or category.get('status') == 2: raise Exception("Category not found")
            return ResponseBuilder.success(data=category, message="Category retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class ItemUnitService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                unit = TenantQuery.createRecord(ItemUnit, data, request)
                return ResponseBuilder.success(data=unit, message="Unit created successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, unit_id):
        try:
            with transaction.atomic():
                unit = TenantQuery.updateRecordById(ItemUnit, unit_id, data, request)
                if not unit:
                    raise Exception("Unit not found")
                return ResponseBuilder.success(data=unit, message="Unit updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["unit_name", True, True], ["short_name", True, True]]
            options = {'attributes': ['id', 'unit_name', 'short_name', 'status']}
            result = TenantQuery.fetchPaginatedData(ItemUnit, data, fieldConfig, options, request)
            return ResponseBuilder.success(data=result, message="Units retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            units = TenantQuery.findAllRecords(ItemUnit, {}, {'attributes': ['id', 'unit_name', 'short_name'], 'order': ['unit_name']}, request)
            return ResponseBuilder.success(data=units, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
            
    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = TenantQuery.softDeleteById(ItemUnit, data.get('ids'), request)
                if count == 0: raise Exception("Already deleted")
                return ResponseBuilder.success(message="Units deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
    
    @staticmethod
    def getById(unit_id, request):
        try:
            unit = TenantQuery.findOneRecord(ItemUnit, unit_id, {}, request)
            if not unit or unit.get('status') == 2: raise Exception("Unit not found")
            return ResponseBuilder.success(data=unit, message="Unit retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class ItemService:
    
    @staticmethod
    def create(request, payload: dict):
        try:
            with transaction.atomic():
                import json

                # Handle multiple images metadata and files
                item_images_metadata = payload.pop('item_images', None)
                
                item_images_final = []
                
                if item_images_metadata:
                    try:
                        metadata_list = json.loads(item_images_metadata)
                        
                        for i, meta in enumerate(metadata_list):
                            key = meta.get('key')
                            url = meta.get('url')
                            is_primary = meta.get('is_primary', False)
                            sort_order = meta.get('sort_order', i)
                            
                            # Case 1: New Upload (has key in request.FILES)
                            if key and key in request.FILES:
                                file = request.FILES.get(key)
                                saved = uploadFile(file, subfolder=ITEM_IMG_FOLDER.rstrip('/'))
                                file_url = next(iter(saved.values())) if saved else None
                                
                                if file_url:
                                    item_images_final.append({
                                        "url": f"{ITEM_IMG_FOLDER.rstrip('/')}/{file_url}",
                                        "sort_order": sort_order,
                                        "is_primary": is_primary
                                    })
                            
                            # Case 2: Existing Image (has url)
                            elif url:
                                # Standardize the URL by removing absolute part if present
                                if settings.MEDIA_URL in url:
                                    url = url.split(settings.MEDIA_URL)[-1]
                                
                                item_images_final.append({
                                    "url": url,
                                    "sort_order": sort_order,
                                    "is_primary": is_primary
                                })
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                if item_images_metadata is not None:
                    payload['item_images'] = item_images_final
                
                # Ignore legacy item_image field as requested
                payload.pop('item_image', None)
                opening_stock = Decimal(str(payload.get('opening_stock', "0.00")))
                payload['current_stock'] = opening_stock
                if 'brand' in payload: payload['brand_id'] = payload.pop('brand')
                payload['item_code'] = generateSequentialCode(Item, 'item_code', ITEM_CODE_PREFIX)
                item = TenantQuery.createRecord(Item, payload, request)

                if opening_stock > 0:
                    TenantQuery.createRecord(
                        StockLedger,
                        {
                            "item_id": item["id"],
                            "movement_type": "OPENING_STOCK",
                            "direction": "IN",
                            "quantity": opening_stock,
                            "balance_after": opening_stock,
                            "reference_type": "ITEM",
                            "reference_id": item["id"],
                            "note": "Opening stock at item creation",
                        },
                        request,
                    )
                
                # Handle multiple images
                if item.get('item_images'):
                    for img in item['item_images']:
                        if img.get('url'):
                            url = str(img['url'])
                            if not url.startswith(ITEM_IMG_FOLDER.rstrip('/')):
                                url = f"{ITEM_IMG_FOLDER.rstrip('/')}/{url}"
                            img['url'] = request.build_absolute_uri(settings.MEDIA_URL + url)

                return ResponseBuilder.success(
                    message="Item created successfully",
                    data=item
                )
        except Exception as e:
            return ResponseBuilder.error(str(e))

    @staticmethod
    def update(request, item_id: int, payload: dict):
        try:
            with transaction.atomic():

                # Handle multiple images metadata and files
                item_images_metadata = payload.pop('item_images', None)
                
                item_images_final = []
                
                if item_images_metadata:
                    try:
                        metadata_list = json.loads(item_images_metadata)
                        
                        for i, meta in enumerate(metadata_list):
                            key = meta.get('key')
                            url = meta.get('url')
                            
                            is_primary = meta.get('is_primary', False)
                            sort_order = meta.get('sort_order', i)
                            
                            found = False
                            # Case 1: New Upload (has key in request.FILES)
                            if key and key in request.FILES:
                                file = request.FILES.get(key)
                                saved = uploadFile(file, subfolder=ITEM_IMG_FOLDER.rstrip('/'))
                                file_url = next(iter(saved.values())) if saved else None
                                
                                if file_url:
                                    item_images_final.append({
                                        "url": f"{ITEM_IMG_FOLDER.rstrip('/')}/{file_url}",
                                        "sort_order": sort_order,
                                        "is_primary": is_primary
                                    })
                                    found = True
                            
                            # Case 2: Existing Image (has url)
                            if not found and url:
                                # Standardize the URL by removing absolute part if present
                                if settings.MEDIA_URL in url:
                                    url = url.split(settings.MEDIA_URL)[-1]
                                
                                item_images_final.append({
                                    "url": url,
                                    "sort_order": sort_order,
                                    "is_primary": is_primary
                                })
                                found = True
                            
                            if not found:
                                pass
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                if item_images_metadata is not None:
                    payload['item_images'] = item_images_final
                
                payload.pop('item_image', None)
                payload.pop('opening_stock', None)
                payload.pop('current_stock', None)
                
                if 'brand' in payload: payload['brand_id'] = payload.pop('brand')
                
                item = TenantQuery.updateRecordById(Item, item_id, payload, request)
                if not item:
                    raise Exception("Item not found")
                
                # Post-process response to return absolute URIs
                if item.get('item_images'):
                    for img in item['item_images']:
                        if img.get('url'):
                            url = str(img['url'])
                            if not url.startswith(ITEM_IMG_FOLDER.rstrip('/')):
                                url = f"{ITEM_IMG_FOLDER.rstrip('/')}/{url}"
                            img['url'] = request.build_absolute_uri(settings.MEDIA_URL + url)

                return ResponseBuilder.success(
                    message="Item updated successfully",
                    data=item
                )
        except Exception as e:
            return ResponseBuilder.error(str(e))

    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = TenantQuery.softDeleteById(Item, data.get('ids'), request)
                
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
                ['category', False, True],
                ["brand", False, False],
            ]

            options = {
                'attributes': [
                    "id",
                    "item_code",
                    "item_name",
                    "item_weight",
                    "category__category_name",
                    "primary_unit__short_name",
                    "current_stock",
                    "selling_price",
                    "brand__brand_name",
                    "status",
                    "item_images"
                ]
            }

            result = TenantQuery.fetchPaginatedData(
                Item, data, fieldConfig, options, request
            )
            
            # Post-process to rename keys for a cleaner response and process images
            for item in result.get('items', []):
                item['category'] = item.pop('category__category_name', None)
                item['brand'] = item.pop('brand__brand_name', None)
                item['unit'] = item.pop('primary_unit__short_name', None)

                
                # Filter item_images to only include primary image (is_primary: true)
                if item.get('item_images'):
                    primary_images = [img for img in item['item_images'] if img.get('is_primary') == True]
                    
                    # Convert relative URLs to absolute URLs for primary images
                    for img in primary_images:
                        if img.get('url'):
                            url = str(img['url'])
                            if not url.startswith(ITEM_IMG_FOLDER.rstrip('/')):
                                url = f"{ITEM_IMG_FOLDER.rstrip('/')}/{url}"
                            img['url'] = request.build_absolute_uri(settings.MEDIA_URL + url)
                    
                    item['item_images'] = primary_images
                else:
                    item['item_images'] = []

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
            items = TenantQuery.findAllRecords(
                Item, 
                {},
                {'attributes': ['id', 'item_name', 'item_code', 'primary_unit__short_name', 'selling_price', 'current_stock', 'description', 'item_images'], 'order': ['item_name']},
                request
            )

            # Post-process to rename keys for a cleaner response and filter primary images
            for item in items:
                item['unit'] = item.pop('primary_unit__short_name', None)
                
                # Filter item_images to only include primary image (is_primary: true)
                if item.get('item_images'):
                    primary_images = [img for img in item['item_images'] if img.get('is_primary') == True]
                    
                    # Convert relative URLs to absolute URLs for primary images
                    for img in primary_images:
                        if img.get('url'):
                            url = str(img['url'])
                            if not url.startswith(ITEM_IMG_FOLDER.rstrip('/')):
                                url = f"{ITEM_IMG_FOLDER.rstrip('/')}/{url}"
                            img['url'] = request.build_absolute_uri(settings.MEDIA_URL + url)
                    
                    item['item_images'] = primary_images
                else:
                    item['item_images'] = []
            
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
            item = TenantQuery.findOneRecord(Item, item_id, {}, request)
            if not item or item.get('status') == 2: raise Exception("Item not found")
            
            # Add full image URL if item_image exists (legacy)
            if item.get('item_image'):
                item['item_image'] = request.build_absolute_uri(settings.MEDIA_URL + str(item['item_image']))
            else:
                item['item_image'] = None
            
            # Add full image URLs for multiple images
            if item.get('item_images'):
                for img in item['item_images']:
                    if img.get('url'):
                        url = str(img['url'])
                        if not url.startswith(ITEM_IMG_FOLDER.rstrip('/')):
                            url = f"{ITEM_IMG_FOLDER.rstrip('/')}/{url}"
                        img['url'] = request.build_absolute_uri(settings.MEDIA_URL + url)
            
            return ResponseBuilder.success(data=item, message="Item retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class InventoryService:
    INWARD_TYPES = {"PURCHASE", "SALES_RETURN", "TRANSFER_IN", "ADJUSTMENT_IN"}
    OUTWARD_TYPES = {
        "SALE",
        "PURCHASE_RETURN",
        "TRANSFER_OUT",
        "DAMAGE",
        "ADJUSTMENT_OUT",
        "SAMPLE_GIVEN",
        "INTERNAL_USE",
        "THEFT_LOSS",
        "DAMAGE_EXPIRED",
    }
    ALLOWED_TYPES = INWARD_TYPES | OUTWARD_TYPES

    @staticmethod
    def applyStockMovement(
        request,
        item_id: int,
        movement_type: str,
        quantity,
        note: str = None,
        reference_type: str = None,
        reference_id: int = None,
    ):
        movement_type = str(movement_type or "").upper().strip()
        if movement_type not in InventoryService.ALLOWED_TYPES:
            raise Exception("Invalid movement_type")

        try:
            qty = Decimal(str(quantity))
        except (InvalidOperation, TypeError, ValueError):
            raise Exception("Invalid quantity")

        if qty <= 0:
            raise Exception("Quantity must be greater than 0")

        item = TenantQuery.findOneRecordForUpdate(
            Item, {"id": item_id}, request
        )
        if not item:
            raise Exception("Item not found")

        is_inward = movement_type in InventoryService.INWARD_TYPES
        if not is_inward and item.current_stock < qty:
            raise Exception(f"Insufficient stock for item {item.item_name}")

        if is_inward:
            new_balance = item.current_stock + qty
            direction = "IN"
        else:
            new_balance = item.current_stock - qty
            direction = "OUT"

        item.current_stock = new_balance
        item.save(update_fields=["current_stock", "updated_at"])

        TenantQuery.createRecord(
            StockLedger,
            {
                "item_id": item.id,
                "movement_type": movement_type,
                "direction": direction,
                "quantity": qty,
                "balance_after": new_balance,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "note": note,
            },
            request,
        )

        return {
            "item_id": item.id,
            "item_name": item.item_name,
            "movement_type": movement_type,
            "quantity": qty,
            "current_stock": new_balance,
        }

    @staticmethod
    def adjust_stock(request, payload: dict):
        try:
            with transaction.atomic():
                result = InventoryService.applyStockMovement(
                    request,
                    item_id=payload["item_id"],
                    movement_type=payload["movement_type"],
                    quantity=payload["quantity"],
                    note=payload.get("note"),
                    reference_type=payload.get("reference_type"),
                    reference_id=payload.get("reference_id"),
                )

            return ResponseBuilder.success(
                message="Stock updated successfully",
                data=result
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getStockTransactions(data, request):
        try:
            fieldConfig = [
                ["item__item_name", True, True],
                ["movement_type", True, True],
                ["direction", True, True],
                ["quantity", True, True],
            ]

            options = {
                "attributes": [
                    "id",
                    "item__item_name",
                    "movement_type",
                    "direction",
                    "quantity",
                    "balance_after",
                    "reference_type",
                    "reference_id",
                    "note",
                    "created_at",
                ]
            }

            result = TenantQuery.fetchPaginatedData(
                StockLedger, data, fieldConfig, options, request
            )

            for row in result.get("items", []):
                row["item_name"] = row.pop("item__item_name", None)

            return ResponseBuilder.success(
                data=result,
                message="Stock transactions retrieved successfully"
            )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
