from typing import Optional
from ninja import Schema, ModelSchema
from pydantic import Field
from decimal import Decimal
from .models import Party


class BrandCreateSchema(Schema):
    brand_name: str = Field(..., min_length=1)


class BrandUpdateSchema(Schema):
    brand_name: str = Field(..., min_length=1)


class TaxCreateSchema(Schema):
    tax_name: str = Field(..., min_length=1)
    tax_value: Decimal = Field(..., ge=0)


class TaxUpdateSchema(Schema):
    tax_name: str = Field(..., min_length=1)
    tax_value: Decimal = Field(..., ge=0)

class PartyCreateSchema(Schema):
    name: str
    party_type: int
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city_id: Optional[int] = None
    state_id: Optional[int] = None
    country_id: Optional[int] = None
    pincode: Optional[str] = None
    balance_type: Optional[int] = None
    customer_category: Optional[int] = None

class PartyUpdateSchema(Schema):
    name: str
    party_type: int
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city_id: Optional[int] = None
    state_id: Optional[int] = None
    country_id: Optional[int] = None
    pincode: Optional[str] = None
    balance_type: Optional[int] = None
    customer_category: Optional[int] = None

class PartyOut(ModelSchema):
    class Meta:
        model = Party
        fields = '__all__'
