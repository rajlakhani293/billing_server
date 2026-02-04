# from ninja import Router
# from apps.core.auth import AuthBearer
# from .schema import SalesCreateSchema, SalesFilterSchema, RevokeSchema
# from .service import SalesService

# sales_router = Router(tags=['Sales'], auth=AuthBearer())

# # Create Sales
# @sales_router.post('/')
# def create(request, payload: SalesCreateSchema):
#     return SalesService.create(payload.dict(), request)

# # Revoke Sales (Soft Delete)
# @sales_router.post('/revoke')
# def revoke(request, payload: RevokeSchema):
#     return SalesService.revoke(payload.dict(), request)

# # Get All Sales
# @sales_router.post('/get-transactions')
# def getAll(request, payload: SalesFilterSchema):
#     return SalesService.getAll(payload.dict(), request)
