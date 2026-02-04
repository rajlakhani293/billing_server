from ninja import Router
from apps.core.auth import AuthBearer
from .service import PartyService
from apps.core.schema import DeleteSchema
from .schema import PartyCreateSchema, PartyUpdateSchema

parties_router = Router(tags=['Parties'], auth=AuthBearer())

# Create Party
@parties_router.post('/')
def create(request, payload: PartyCreateSchema):
    return PartyService.create(payload.dict(), request)

# Delete Parties
@parties_router.delete('/delete')
def delete(request, payload: DeleteSchema):
    return PartyService.delete(payload.dict(), request)

# Get Dropdown
@parties_router.get('/dropdown-list')
def dropdownList(request):
    return PartyService.dropdownList(request)

# Get All Parties
@parties_router.post('/get-transactions')
def getAll(request, payload: dict = None):
    return PartyService.getAll(payload, request)

# Update Party
@parties_router.put('/{party_id}')
def update(request, party_id: int, payload: PartyUpdateSchema):
    return PartyService.update(payload.dict(), request, party_id)

# Get Party by ID
@parties_router.get('/{party_id}')
def getById(request, party_id: int):
    return PartyService.getById(party_id, request)
