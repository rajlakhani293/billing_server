from ninja import Schema
from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import field_validator, model_validator

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

class SalesReturnTransactionIn(Schema):
    sales_transaction_id: int
    return_quantity: Decimal

    @field_validator('return_quantity', mode='before')
    @classmethod
    def validate_return_quantity(cls, v):
        try:
            qty = Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Return quantity must be a valid decimal number")

        if qty <= 0:
            raise ValueError("Return quantity must be greater than 0")
        return qty

class SalesIn(Schema):
    party_id: Optional[int] = None
    sales_date: Optional[date] = None
    # Financials
    subtotal: Decimal
    tax_amount: Optional[Decimal] = 0.00
    discount_amount: Optional[Decimal] = 0.00
    discount_percentage: Optional[Decimal] = 0.00
    total_amount: Decimal
    paid_amount: Decimal = Decimal("0.00")
    
    # Payment and Status
    payment_mode: int = 1
    notes: Optional[str] = None
    
    # Transactions
    transactions: List[SalesTransactionSchema]

    @field_validator('party_id', mode='before')
    @classmethod
    def validate_party_id(cls, v, info):
        if v == "" or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError("Party ID must be a valid integer")

    @field_validator('payment_mode', mode='before')
    @classmethod
    def validate_payment_mode(cls, v, info):
        if v == "" or v is None:
            return 1
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError("Payment mode must be a valid integer")

    @field_validator('paid_amount', mode='before')
    @classmethod
    def validate_decimal_fields(cls, v):
        if v == "" or v is None:
            return Decimal("0.00")
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Value must be a valid decimal number")

    @field_validator('discount_amount', mode='before')
    @classmethod
    def validate_discount_amount(cls, v):
        if v == "" or v is None:
            return Decimal("0.00")
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Discount value must be a valid decimal number")

    @model_validator(mode='after')
    def validate_model(self):
        if self.payment_mode == 3:
            if not self.party_id:
                raise ValueError("Party ID is required when payment mode is Partial")
            if self.paid_amount < 0:
                raise ValueError("Paid amount must be 0 or greater when payment mode is Partial")
        return self

class SalesUpdateIn(Schema):
    return_notes: Optional[str] = None
    update_notes: Optional[str] = None
    paid_amount: Optional[Decimal] = None
    payment_mode: Optional[int] = None
    return_transactions: Optional[List[SalesReturnTransactionIn]] = []
    add_transactions: Optional[List[SalesTransactionSchema]] = []

    @field_validator('payment_mode', mode='before')
    @classmethod
    def validate_update_payment_mode(cls, v):
        if v == "" or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError("Payment mode must be a valid integer")

    @field_validator('paid_amount', mode='before')
    @classmethod
    def validate_update_paid_amount(cls, v):
        if v == "" or v is None:
            return None
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Paid amount must be a valid decimal number")

class SalesRevertIn(Schema):
    notes: Optional[str] = None
