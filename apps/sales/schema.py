from ninja import Schema
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class SalesTransactionCreateSchema(Schema):
    item_id: int
    item_description: str
    item_quantity: Decimal
    item_rate: Decimal
    discount_percentage: Optional[Decimal] = 0.00
    discount_amount: Optional[Decimal] = 0.00
    tax_amount: Optional[Decimal] = 0.00
    total_amount: Decimal


class SalesCreateSchema(Schema):
    sales_date: datetime
    party_id: Optional[int] = None
    payment_mode: int
    notes: Optional[str] = None
    
    # Financials
    subtotal: Decimal
    tax_amount: Optional[Decimal] = 0.00
    discount_percentage: Optional[Decimal] = 0.00
    discount_amount: Optional[Decimal] = 0.00
    total_amount: Decimal
    paid_amount: Decimal
    
    # Nested transactions
    transactions: List[SalesTransactionCreateSchema]


class SalesFilterSchema(Schema):
    page: Optional[int] = 1
    limit: Optional[int] = 10
    search: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    status: Optional[int] = None
    payment_mode: Optional[int] = None
    party_id: Optional[int] = None
    sortBy: Optional[str] = "created_at"
    sortDirection: Optional[str] = "descending"


class RevokeSchema(Schema):
    ids: List[int]

