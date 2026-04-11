
from ninja.router import Router
from apps.accounts.auth_service import AuthService
from apps.core.auth import AuthBearer
from apps.core.schema import DeleteSchema, PartyCreditDaysSchema
from .schema import BrandCreateSchema, BrandUpdateSchema, TaxCreateSchema, TaxUpdateSchema, PartyCreateSchema, PartyUpdateSchema, PartyPaymentSchema
from .service import BrandService, TaxService, PartyService


setting_router = Router(tags=['Setting'], auth=AuthBearer())

# Session Data
@setting_router.get('/session-data')
def session_data(request):
    return AuthService.getSessionData(request)


# ================================================================= ================================================================= =================================================================
# Brand CRUD APIs
# ================================================================= ================================================================= =================================================================

# Create Brand
@setting_router.post('/brands/')
def createBrand(request, payload: BrandCreateSchema):
    return BrandService.create(payload.dict(), request)

# Delete Brands
@setting_router.delete('/brands/delete')
def deleteBrands(request, payload: DeleteSchema):
    return BrandService.delete(payload.dict(), request)

# Get all Brands
@setting_router.post('/brands/get-transactions')
def getAllBrands(request, payload: dict = None):
    return BrandService.getAll(payload, request)

# Get Brand Dropdown
@setting_router.get('/brands/dropdown-list')
def getBrandDropdown(request):
    return BrandService.dropdownList(request)

# Update Brand
@setting_router.put('/brands/{brand_id}')
def updateBrand(request, brand_id: int, payload: BrandUpdateSchema):
    return BrandService.update(payload.dict(), request, brand_id)

# Get Brand by ID
@setting_router.get('/brands/{brand_id}')
def getBrandById(request, brand_id: int):
    return BrandService.getById(brand_id, request)


# ================================================================= ================================================================= =================================================================
# Tax CRUD APIs
# ================================================================= ================================================================= =================================================================

# Create Tax
@setting_router.post('/taxes/')
def createTax(request, payload: TaxCreateSchema):
    return TaxService.create(payload.dict(), request)

# Delete Taxes
@setting_router.delete('/taxes/delete')
def deleteTaxes(request, payload: DeleteSchema):
    return TaxService.delete(payload.dict(), request)

# Get all Taxes
@setting_router.post('/taxes/get-transactions')
def getAllTaxes(request, payload: dict = None):
    return TaxService.getAll(payload, request)

# Get Tax Dropdown
@setting_router.get('/taxes/dropdown-list')
def getTaxDropdown(request):
    return TaxService.dropdownList(request)

# Update Tax
@setting_router.put('/taxes/{tax_id}')
def updateTax(request, tax_id: int, payload: TaxUpdateSchema):
    return TaxService.update(payload.dict(), request, tax_id)

# Get Tax by ID
@setting_router.get('/taxes/{tax_id}')
def getTaxById(request, tax_id: int):
    return TaxService.getById(tax_id, request)


# ================================================================= ================================================================= =================================================================
# Party CRUD APIs
# ================================================================= ================================================================= =================================================================

# Create Party
@setting_router.post('/parties/')
def create(request, payload: PartyCreateSchema):
    return PartyService.create(payload.dict(), request)

# Delete Parties
@setting_router.delete('/parties/delete')
def delete(request, payload: DeleteSchema):
    return PartyService.delete(payload.dict(), request)

# Get Dropdown
@setting_router.get('/parties/dropdown-list')
def dropdownList(request):
    return PartyService.dropdownList(request)

# Get All Parties
@setting_router.post('/parties/get-transactions')
def getAll(request, payload: dict = None):
    return PartyService.getAll(payload, request)

# Update Party
@setting_router.put('/parties/{party_id}')
def update(request, party_id: int, payload: PartyUpdateSchema):
    return PartyService.update(payload.dict(), request, party_id)

# Get Party by ID
@setting_router.get('/parties/{party_id}')
def getById(request, party_id: int):
    return PartyService.getById(party_id, request)

# Party Due List (Sales)
@setting_router.post('/party-due-list')
def getPartyDueList(request, payload: dict = None):
    return PartyService.getPartyDueList(payload, request)

# Payment History
@setting_router.post('/payments/get-transactions')
def getPaymentHistory(request, payload: dict = None):
    return PartyService.getPaymentHistory(payload, request)

# Party Payment (Ledger)
@setting_router.post('/party-payment')
def addPartyPayment(request, payload: PartyPaymentSchema):
    return PartyService.addPayment(payload.dict(), request)

# Party Credit Summary (Sales)
@setting_router.post('/party-credit-summary/{party_id}')
def getPartyCreditDays(request, party_id: int, payload: PartyCreditDaysSchema):
    return PartyService.getPartyCreditDays(party_id, payload.dict(), request)
