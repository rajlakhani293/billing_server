from ninja import Router, Form
from apps.core.auth import AuthBearer
from .service import CompanyService, BranchService
from apps.core.schema import DeleteSchema
from .schema import CompanyUpdateSchema, CompanyCreateSchema, BranchCreateSchema, BranchUpdateSchema
from apps.core.helpers import parseMultipartRequest

company_router = Router(tags=['Company'], auth=AuthBearer())

# ================================================================= ================================================================= =================================================================
# Company CRUD APIs
# ================================================================= ================================================================= =================================================================

@company_router.put("/{company_id}")
def update_company(request, company_id: int, payload: CompanyUpdateSchema = Form(...)):
    request = parseMultipartRequest(request)
    data = payload.dict()
    return CompanyService.update(data, request, company_id)

@company_router.get("/{company_id}")
def getCompanyById(request, company_id: int):
    return CompanyService.getById(company_id, request)

# ================================================================= ================================================================= =================================================================
# Branch CRUD APIs
# ================================================================= ================================================================= =================================================================

@company_router.post("/branches/")
def create_branch(request, payload: BranchCreateSchema):
    return BranchService.create(payload.dict(), request)

@company_router.put("/branches/{branch_id}")
def update_branch(request, branch_id: int, payload: BranchUpdateSchema):
    return BranchService.update(payload.dict(), request, branch_id)

@company_router.get("/branches/{branch_id}")
def getBranchById(request, branch_id: int):
    return BranchService.getById(branch_id, request)

@company_router.get("/branches/dropdown-list")
def getBranchDropdown(request):
    return BranchService.dropdownList(request)

@company_router.post("/branches/get-transactions")
def getAllBranches(request, payload: dict = None):
    return BranchService.getAll(payload, request)

@company_router.delete("/branches/delete")
def deleteBranches(request, payload: DeleteSchema):
    return BranchService.delete(payload.dict(), request)
