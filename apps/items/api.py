from ninja import Router, File, UploadedFile, Form
from apps.core.auth import AuthBearer
from .service import ItemService, ItemCategoryService, ItemUnitService, BrandService, TaxService
from apps.core.schema import DeleteSchema
from .schema import ItemCategoryCreateSchema, ItemCategoryUpdateSchema, ItemUnitUpdateSchema, ItemUnitCreateSchema, ItemIn, BrandCreateSchema, BrandUpdateSchema, TaxCreateSchema, TaxUpdateSchema

# ================================================================= ================================================================= =================================================================
# Items CRUD APIs
# ================================================================= ================================================================= =================================================================
items_router = Router(tags=['Items'], auth=AuthBearer())


@items_router.post("/")
def create_item(request, payload: ItemIn = Form(...), item_image: UploadedFile = File(None)):
    return ItemService.create(request, payload.dict(), item_image)

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


# ================================================================= ================================================================= =================================================================
# Brand CRUD APIs
# ================================================================= ================================================================= =================================================================

# Create Brand
@items_router.post('/brands/')
def createBrand(request, payload: BrandCreateSchema):
    return BrandService.create(payload.dict(), request)

# Delete Brands
@items_router.delete('/brands/delete')
def deleteBrands(request, payload: DeleteSchema):
    return BrandService.delete(payload.dict(), request)

# Get all Brands
@items_router.post('/brands/get-transactions')
def getAllBrands(request, payload: dict = None):
    return BrandService.getAll(payload, request)

# Get Brand Dropdown
@items_router.get('/brands/dropdown-list')
def getBrandDropdown(request):
    return BrandService.dropdownList(request)

# Update Brand
@items_router.put('/brands/{brand_id}')
def updateBrand(request, brand_id: int, payload: BrandUpdateSchema):
    return BrandService.update(payload.dict(), request, brand_id)

# Get Brand by ID
@items_router.get('/brands/{brand_id}')
def getBrandById(request, brand_id: int):
    return BrandService.getById(brand_id, request)


# ================================================================= ================================================================= =================================================================
# Tax CRUD APIs
# ================================================================= ================================================================= =================================================================

# Create Tax
@items_router.post('/taxes/')
def createTax(request, payload: TaxCreateSchema):
    return TaxService.create(payload.dict(), request)

# Delete Taxes
@items_router.delete('/taxes/delete')
def deleteTaxes(request, payload: DeleteSchema):
    return TaxService.delete(payload.dict(), request)

# Get all Taxes
@items_router.post('/taxes/get-transactions')
def getAllTaxes(request, payload: dict = None):
    return TaxService.getAll(payload, request)

# Get Tax Dropdown
@items_router.get('/taxes/dropdown-list')
def getTaxDropdown(request):
    return TaxService.dropdownList(request)

# Update Tax
@items_router.put('/taxes/{tax_id}')
def updateTax(request, tax_id: int, payload: TaxUpdateSchema):
    return TaxService.update(payload.dict(), request, tax_id)

# Get Tax by ID
@items_router.get('/taxes/{tax_id}')
def getTaxById(request, tax_id: int):
    return TaxService.getById(tax_id, request)