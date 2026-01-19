from ninja import Router
from apps.core.auth import AuthBearer
from .schema import (
    PartyCreateSchema,
    PartyUpdateSchema,
    PartyStatusUpdateSchema,
    PartyFilterSchema
)
from .service import PartyService

parties_router = Router(tags=['Parties'], auth=AuthBearer())

# ================================================================= ================================================================= =================================================================
# Parties CRUD APIs
# ================================================================= ================================================================= =================================================================

# Create Party
@parties_router.post('/')
def create(request, payload: PartyCreateSchema):
    return PartyService.create(payload.dict(), request)

# Get all Parties with pagination and filtering
@parties_router.post('/get-transactions')
def getAll(request, payload: PartyFilterSchema):
    return PartyService.getAll(payload.dict(), request)

# Get Party Dropdown List
@parties_router.get('/dropdown-list')
def dropdownList(request):
    return PartyService.dropdownList(request)

# # Update Party Status (active/inactive)
# @parties_router.patch('/status')
# def updateStatus(request, payload: PartyStatusUpdateSchema):
#     return PartyService.updateStatus(payload.dict(), request)

# # Get Party by ID
# @parties_router.get('/{party_id}')
# def getById(request, party_id: str):
#     return PartyService.getById(party_id, request)

# # Update Party
# @parties_router.put('/{party_id}')
# def update(request, party_id: str, payload: PartyUpdateSchema):
#     return PartyService.update(payload.dict(), request, party_id)

# # Delete Party (soft delete)
# @parties_router.delete('/{party_id}')
# def delete(request, party_id: str):
#     return PartyService.delete(party_id, request)

