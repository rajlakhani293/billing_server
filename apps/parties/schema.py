from ninja import Schema
from typing import Optional
from datetime import datetime


class PartyCreateSchema(Schema):
    name: str
    party_type: int
    customer_category: int
    phone_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[int] = None
    state: Optional[int] = None
    country: Optional[int] = None
    pincode: Optional[str] = None
    wallet_balance: Optional[float] = 0.00
    balance_type: Optional[int] = None


class PartyUpdateSchema(Schema):
    name: str
    party_type: int
    phone_number: str
    customer_category: int
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[int] = None
    state: Optional[int] = None
    country: Optional[int] = None
    pincode: Optional[str] = None
    wallet_balance: Optional[float] = None
    balance_type: Optional[int] = None


class PartyResponseSchema(Schema):
    id: int
    name: str
    party_type: int
    phone_number: str
    email: Optional[str]
    address: Optional[str]
    city: Optional[dict]
    state: Optional[dict]
    country: Optional[dict]
    pincode: Optional[str]
    wallet_balance: float
    balance_type: Optional[int]
    customer_category: int
    status: int
    shop: int
    
    class Config:
        from_attributes = True


class PartyDropdownSchema(Schema):
    id: int
    name: str
    party_type: int
    phone_number: str
    email: Optional[str]
    
    class Config:
        from_attributes = True


class PartyStatusUpdateSchema(Schema):
    id: int
    status: int


class PartyFilterSchema(Schema):
    page: Optional[int] = 1
    limit: Optional[int] = 10
    search: Optional[str] = None
    party_type: Optional[int] = None
    status: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    sortBy: Optional[str] = "created_at"
    sortDirection: Optional[str] = "descending"
    user_id: Optional[int] = None
    shop_id: Optional[int] = None


class SuccessResponseSchema(Schema):
    success: bool
    code: int
    message: str


class ErrorResponseSchema(Schema):
    success: bool
    code: int
    message: str
    errors: Optional[dict] = None
