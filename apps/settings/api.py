
from ninja.router import Router
from ninja import Form
from apps.accounts.auth_service import AuthService
from apps.core.auth import AuthBearer
from apps.core.schema import DeleteSchema, PartyCreditDaysSchema
from .schema import BrandCreateSchema, BrandUpdateSchema, TaxCreateSchema, TaxUpdateSchema, PartyCreateSchema, PartyUpdateSchema, PartyPaymentSchema
from .service import BrandService, TaxService, PartyService, CompanyService, BranchService, UserService
from apps.company.schema import CompanyUpdateSchema, BranchCreateSchema, BranchUpdateSchema
from apps.accounts.schema import UserUpdateSchema, UserPasswordUpdateSchema, SendPasswordOTPSchema
from apps.core.helpers import parseMultipartRequest


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


# ================================================================= ================================================================= =================================================================
# Company CRUD APIs
# ================================================================= ================================================================= =================================================================

@setting_router.put("/companies/{company_id}")
def update_company(request, company_id: int, payload: CompanyUpdateSchema = Form(...)):
    request = parseMultipartRequest(request)
    return CompanyService.update(payload.dict(), request, company_id)

@setting_router.get("/companies/{company_id}")
def getCompanyById(request, company_id: int):
    return CompanyService.getById(company_id, request)

# ================================================================= ================================================================= =================================================================
# User CRUD APIs
# ================================================================= ================================================================= =================================================================

@setting_router.post("/users/send-password-otp")
def send_password_otp(request, payload: SendPasswordOTPSchema):
    return UserService.sendPasswordOTP(payload.phone_number, request)

@setting_router.post("/users/update-password")
def update_user_password(request, payload: UserPasswordUpdateSchema):
    return UserService.updatePasswordWithOTP(payload.dict(), request)

@setting_router.put("/users/{user_id}")
def update_user(request, user_id: int, payload: UserUpdateSchema = Form(...)):
    request = parseMultipartRequest(request)
    return UserService.update(payload.dict(), request, user_id)

@setting_router.get("/users/{user_id}")
def getUserById(request, user_id: int):
    return UserService.getById(user_id, request)

# ================================================================= ================================================================= =================================================================
# Branch CRUD APIs
# ================================================================= ================================================================= =================================================================

@setting_router.post("/branches/")
def create_branch(request, payload: BranchCreateSchema):
    return BranchService.create(payload.dict(), request)

@setting_router.post("/branches/get-transactions")
def getAllBranches(request, payload: dict = None):
    return BranchService.getAll(payload, request)

@setting_router.put("/branches/{branch_id}")
def update_branch(request, branch_id: int, payload: BranchUpdateSchema):
    return BranchService.update(payload.dict(), request, branch_id)

@setting_router.get("/branches/{branch_id}")
def getBranchById(request, branch_id: int):
    return BranchService.getById(branch_id, request)

@setting_router.delete("/branches/delete")
def deleteBranches(request, payload: DeleteSchema):
    return BranchService.delete(payload.dict(), request)

@setting_router.get("/branches/switch/{branch_id}")
def switchBranch(request, branch_id: int):
    return BranchService.switchBranch(branch_id, request)

@setting_router.get("/branches-dropdown")
def getBranchDropdown(request):
    return BranchService.dropdownList(request)
