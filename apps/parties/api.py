from ninja import Router
from apps.core.auth import AuthBearer
from apps.core.helpers import handle_response, handle_not_found_response
from .schema import (
    PartyCreateSchema,
    PartyUpdateSchema,
    PartyResponseSchema,
    PartyDropdownSchema,
    PartyStatusUpdateSchema,
    PartyFilterSchema,
    SuccessResponseSchema,
    ErrorResponseSchema
)
from .service import PartyService

parties_router = Router(tags=['Parties'])

# ================================================================= ================================================================= =================================================================
# Parties CRUD APIs
# ================================================================= ================================================================= =================================================================

# Create Party
# @parties_router.post('/', response={200: PartyResponseSchema, 400: ErrorResponseSchema},auth=AuthBearer())
# def create(request, payload: PartyCreateSchema):
#     result = PartyService.create(payload.dict(), request)
#     return handle_response(result)

@parties_router.post('/', response={200: PartyResponseSchema, 400: ErrorResponseSchema}, auth=AuthBearer())
def create(request, payload: PartyCreateSchema):
    return PartyService.create(request, payload)

# Update Party
@parties_router.put('/{party_id}', response={200: PartyResponseSchema, 400: ErrorResponseSchema},auth=AuthBearer())
def update(request, party_id: str, payload: PartyUpdateSchema):
    payload_dict = payload.dict()
    payload_dict['id'] = party_id
    result = PartyService.update(payload_dict, request)
    return handle_not_found_response(result, "Party not found")

# Get all Parties with pagination and filtering
@parties_router.post('/get-transactions', response={200: dict, 400: ErrorResponseSchema},auth=AuthBearer())
def getAll(request, payload: PartyFilterSchema):
    result = PartyService.getAll(payload.dict(), request)
    return handle_response(result)

# Get Party by ID
@parties_router.get('/{party_id}', response={200: PartyResponseSchema, 400: ErrorResponseSchema},auth=AuthBearer())
def getById(request, party_id: str):
    result = PartyService.getById(party_id, request)
    return handle_not_found_response(result, "Party not found")

# Delete Party (soft delete)
@parties_router.delete('/{party_id}', response={200: SuccessResponseSchema, 400: ErrorResponseSchema},auth=AuthBearer())
def delete(request, party_id: str):
    result = PartyService.delete(party_id, request)
    return handle_not_found_response(result, "Party not found")

# Update Party Status (active/inactive)
@parties_router.patch('/status', response={200: PartyResponseSchema, 400: ErrorResponseSchema},auth=AuthBearer())
def updateStatus(request, payload: PartyStatusUpdateSchema):
    result = PartyService.updateStatus(payload.dict(), request)
    return handle_not_found_response(result, "Party not found")

# Get Party Dropdown List
@parties_router.post('/dropdown-list', response={200: list[PartyDropdownSchema], 400: ErrorResponseSchema},auth=AuthBearer())
def dropdownList(request, payload: dict = None):
    if payload is None:
        payload = {}
    result = PartyService.dropdownList(payload, request)
    return handle_response(result)

