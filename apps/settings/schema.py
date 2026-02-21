from ninja import Schema
from pydantic import Field
from decimal import Decimal


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
