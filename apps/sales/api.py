from ninja import Router
from apps.core.auth import AuthBearer
from .service import SalesService
from apps.core.schema import DeleteSchema
from .schema import SalesIn

sales_router = Router(tags=['Sales'], auth=AuthBearer())

@sales_router.post("/")
def create_sales(request, payload: SalesIn):
    return SalesService.create(request, payload.dict())

@sales_router.delete('/delete')
def delete(request, payload: DeleteSchema):
    return SalesService.delete(payload.dict(), request)

@sales_router.post('/get-transactions')
def getAll(request, payload: dict = None):
    return SalesService.getAll(payload, request)

@sales_router.get('/{sales_id}')
def getSalesById(request, sales_id: int):
    return SalesService.getById(sales_id, request)
