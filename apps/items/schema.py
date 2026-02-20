from ninja import Field, Schema
from typing import Optional
from decimal import Decimal

class ItemDropdownSchema(Schema):
    id: int
    item_name: str
    item_code: str
    current_stock: Decimal
    selling_price: Decimal
    item_image: Optional[str] = None
    
    class Config:
        from_attributes = True

class ItemStatusUpdateSchema(Schema):
    id: int
    status: int

class ItemCategoryCreateSchema(Schema):
    category_name: str = Field(..., min_length=1)
    description: Optional[str] = None

class ItemCategoryUpdateSchema(Schema):
    category_name: str = Field(..., min_length=1)
    description: Optional[str] = None

class ItemUnitCreateSchema(Schema):
    unit_name: str = Field(..., min_length=1)
    short_name: str = Field(..., min_length=1)

class ItemUnitUpdateSchema(Schema):
    unit_name: str = Field(..., min_length=1)
    short_name: str = Field(..., min_length=1)

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

class ItemIn(Schema):
    item_code: Optional[str] = None
    item_name: str = Field(..., min_length=1)
    category_id: int
    description: Optional[str] = None
    purchase_price: Optional[Decimal] = Decimal("0.00")
    selling_price: Decimal = Decimal("0.00")
    tax: Optional[int] = None
    hsn_code: Optional[str] = None
    opening_stock: Optional[Decimal] = Decimal("0.00")
    min_stock_level: Optional[Decimal] = Decimal("0.00")
    max_stock_level: Optional[Decimal] = Decimal("0.00")
    primary_unit_id: int
    item_weight: Optional[Decimal] = None
    brand_id: Optional[int] = None
    barcode: Optional[str] = None
