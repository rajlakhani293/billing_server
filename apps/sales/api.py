from ninja import Router
from apps.core.auth import AuthBearer
from .service import SalesService
from .schema import SalesIn, SalesReturnIn, SalesRevertIn

sales_router = Router(tags=['Sales'], auth=AuthBearer())

@sales_router.post("/")
def create_sales(request, payload: SalesIn):
    return SalesService.create(request, payload.dict())

@sales_router.post('/get-transactions')
def getAll(request, payload: dict = None):
    return SalesService.getAll(payload, request)

@sales_router.get('/{sales_id}')
def getSalesById(request, sales_id: int):
    return SalesService.getById(sales_id, request)

@sales_router.post('/{sales_id}/returns')
def createSalesReturn(request, sales_id: int, payload: SalesReturnIn):
    return SalesService.createReturn(request, sales_id, payload.dict())

@sales_router.post('/{sales_id}/revert')
def revertSales(request, sales_id: int, payload: SalesRevertIn):
    return SalesService.revertSale(request, sales_id, payload.dict())
