
from ninja.router import Router
from apps.accounts.auth_service import AuthService
from apps.core.auth import AuthBearer
from apps.core.schema import DeleteSchema
from .schema import BrandCreateSchema, BrandUpdateSchema, TaxCreateSchema, TaxUpdateSchema
from .service import BrandService, TaxService


setting_router = Router(tags=['Setting'])

# Session Data
@setting_router.get('/session-data', auth=AuthBearer())
def session_data(request):
    return AuthService.get_session_data(request)


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