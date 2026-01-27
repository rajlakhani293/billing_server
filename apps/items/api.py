from ninja import Router
from apps.core.auth import AuthBearer
from .service import ItemService
from apps.core.schema import DeleteSchema, UpdateStatusSchema
items_router = Router(tags=['Items'], auth=AuthBearer())

# ================================================================= ================================================================= =================================================================
# Items CRUD APIs
# ================================================================= ================================================================= =================================================================

# Create Item
@items_router.post('/')
def create(request, payload: dict):
    return ItemService.create(payload, request)

# Delete Items (soft delete)
@items_router.delete('/delete')
def delete(request, payload: DeleteSchema):
    return ItemService.delete(payload.dict(), request)

# Get all Items with pagination and filtering
@items_router.post('/get-transactions')
def getAll(request, payload: dict = None):
    return ItemService.getAll(payload, request)

# Get Item Dropdown List
@items_router.get('/dropdown-list')
def dropdownList(request):
    return ItemService.dropdownList(request)

# Update Item Status (Active/Inactive)
@items_router.patch('/status')
def updateStatus(request, payload: UpdateStatusSchema):
    return ItemService.updateStatus(payload.dict(), request)

# Update Item
@items_router.put('/{item_id}')
def update(request, item_id: int, payload: dict):
    return ItemService.update(payload, request, item_id)

# Get Item by ID
@items_router.get('/{item_id}')
def getById(request, item_id: int):
    return ItemService.getById(item_id, request)


