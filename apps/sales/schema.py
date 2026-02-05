from ninja import Schema
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class SalesTransactionSchema(Schema):
    item_id: int
    item_quantity: Decimal
    item_rate: Decimal
    item_description: Optional[str] = None
    discount_percentage: Optional[Decimal] = 0.00
    discount_amount: Optional[Decimal] = 0.00
    tax_amount: Optional[Decimal] = 0.00
    total_amount: Decimal

    class Config:
        from_attributes = True

class SalesIn(Schema):
    party_id: Optional[int] = None
    sales_date: datetime
    # Financials
    subtotal: Decimal
    tax_amount: Optional[Decimal] = 0.00
    discount_percentage: Optional[Decimal] = 0.00
    discount_amount: Optional[Decimal] = 0.00
    total_amount: Decimal
    paid_amount: Decimal = Decimal("0.00")
    
    # Payment and Status
    payment_mode: int = 1
    notes: Optional[str] = None
    
    # Transactions
    transactions: List[SalesTransactionSchema]

class SalesUpdateSchema(Schema):
    party_id: Optional[int] = None
    sales_date: Optional[datetime] = None
    subtotal: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    payment_mode: Optional[int] = None
    notes: Optional[str] = None
