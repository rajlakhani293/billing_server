from typing import List
from ninja import Router, File, UploadedFile, Form
from apps.core.auth import AuthBearer
from .service import ItemService, ItemCategoryService, ItemUnitService
from apps.core.schema import DeleteSchema
from .schema import ItemCategoryCreateSchema, ItemCategoryUpdateSchema, ItemUnitUpdateSchema, ItemUnitCreateSchema, ItemIn, ItemUpdateSchema
from apps.core.helpers import parse_multipart_request

# ================================================================= ================================================================= =================================================================
# Items CRUD APIs
# ================================================================= ================================================================= =================================================================
items_router = Router(tags=['Items'], auth=AuthBearer())


@items_router.post("/")
def create_item(request, payload: ItemIn = Form(...)):
    return ItemService.create(request, payload.dict())

@items_router.delete('/delete')
def delete(request, payload: DeleteSchema):
    return ItemService.delete(payload.dict(), request)

@items_router.post('/get-transactions')
def getAll(request, payload: dict = None):
    return ItemService.getAll(payload, request)

@items_router.get('/dropdown-list')
def dropdownList(request):
    return ItemService.dropdownList(request)

@items_router.get('/{item_id}')
def getItemById(request, item_id: int):
    return ItemService.getById(item_id, request)

@items_router.put("/{item_id}")
def update_item(request, item_id: int, payload: ItemUpdateSchema = Form(...)):
    request = parse_multipart_request(request)
    return ItemService.update(request, item_id, payload.dict())

# ================================================================= ================================================================= =================================================================
# Item Category CRUD APIs
# ================================================================= ================================================================= =================================================================

# Create Category
@items_router.post('/categories/')
def createCategory(request, payload: ItemCategoryCreateSchema):
    return ItemCategoryService.create(payload.dict(), request)

# Delete Categories
@items_router.delete('/categories/delete')
def deleteCategories(request, payload: DeleteSchema):
    return ItemCategoryService.delete(payload.dict(), request)

# Get all Categories
@items_router.post('/categories/get-transactions')
def getAllCategories(request, payload: dict = None):
    return ItemCategoryService.getAll(payload, request)

# Get Category Dropdown
@items_router.get('/categories/dropdown-list')
def getCategoryDropdown(request):
    return ItemCategoryService.dropdownList(request)

# Update Category
@items_router.put('/categories/{category_id}')
def updateCategory(request, category_id: int, payload: ItemCategoryUpdateSchema):
    return ItemCategoryService.update(payload.dict(), request, category_id)

# Get Category by ID
@items_router.get('/categories/{category_id}')
def getCategoryById(request, category_id: int):
    return ItemCategoryService.getById(category_id, request)


# ================================================================= ================================================================= =================================================================
# Item Unit CRUD APIs
# ================================================================= ================================================================= =================================================================

# Get Unit Dropdown
@items_router.get('/units/dropdown-list')
def getUnitDropdown(request):
    return ItemUnitService.dropdownList(request)

# Create Unit
@items_router.post('/units/')
def createUnit(request, payload: ItemUnitCreateSchema):
    return ItemUnitService.create(payload.dict(), request)

# Get all Units
@items_router.post('/units/get-transactions')
def getAllUnits(request, payload: dict = None):
    return ItemUnitService.getAll(payload, request)

# Delete Units
@items_router.delete('/units/delete')
def deleteUnits(request, payload: DeleteSchema):
    return ItemUnitService.delete(payload.dict(), request)

# Update Unit
@items_router.put('/units/{unit_id}')
def updateUnit(request, unit_id: int, payload: ItemUnitUpdateSchema):
    return ItemUnitService.update(payload.dict(), request, unit_id)

# Get Unit by ID
@items_router.get('/units/{unit_id}')
def getUnitById(request, unit_id: int):
    return ItemUnitService.getById(unit_id, request)