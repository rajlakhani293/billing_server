from ninja import Router
from apps.core.auth import AuthBearer
from .service import SalesService
from .schema import SalesIn, SalesRevertIn, SalesUpdateIn, SalesPaymentIn

sales_router = Router(tags=['Sales'], auth=AuthBearer())

@sales_router.post("/")
def create_sales(request, payload: SalesIn):
    return SalesService.create(request, payload.dict())

@sales_router.post('/get-transactions')
def getAll(request, payload: dict = None):
    return SalesService.getAll(payload, request)

@sales_router.post('/ledger/get-transactions')
def getLedgerTransactions(request, payload: dict = None):
    return SalesService.getLedgerTransactions(payload, request)

@sales_router.post('/ledger/get-payments')
def getLedgerPayments(request, payload: dict = None):
    return SalesService.getLedgerPayments(payload, request)

@sales_router.post('/party-credit-summary')
def getPartyCreditSummary(request, payload: dict = None):
    return SalesService.getPartyCreditSummary(payload, request)

@sales_router.post('/party-credit-summary/{party_id}')
def getPartyCreditDays(request, party_id: int, payload: dict = None):
    return SalesService.getPartyCreditDays(party_id, payload, request)

@sales_router.post('/dashboard-stats')
def getDashboardStats(request):
    return SalesService.getDashboardStats(request)

@sales_router.post('/dashboard-charts')
def getDashboardCharts(request, payload: dict = None):
    return SalesService.getSalesCharts(request, payload or {})

@sales_router.post('/dashboard-top-products')
def getDashboardTopProducts(request, payload: dict = None):
    return SalesService.getTopProducts(request, payload or {})

@sales_router.post('/payments')
def createPayment(request, payload: SalesPaymentIn):
    return SalesService.createPayment(request, payload.dict())

@sales_router.get('/{sales_id}')
def getSalesById(request, sales_id: int):
    return SalesService.getById(sales_id, request)

@sales_router.post('/{sales_id}/returns')
def revertSales(request, sales_id: int, payload: SalesRevertIn):
    return SalesService.revertSale(request, sales_id, payload.dict())

@sales_router.put('/{sales_id}')
def updateSales(request, sales_id: int, payload: SalesUpdateIn):
    return SalesService.update(request, sales_id, payload.dict())
