from ninja import Field, Schema
from typing import Optional, Any
from decimal import Decimal
from pydantic import field_validator

class ItemDropdownSchema(Schema):
    id: int
    item_name: str
    item_code: str
    current_stock: Decimal
    selling_price: Decimal
    item_image: Optional[str] = None
    item_images: Optional[list] = None
    
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


class ItemIn(Schema):
    item_code: Optional[str] = None
    item_name: str = Field(..., min_length=1)
    category_id: int
    description: Optional[str] = None
    purchase_price: Optional[Decimal] = Decimal("0.00")
    selling_price: Decimal = Decimal("0.00")
    tax: int
    hsn_code: Optional[str] = None
    opening_stock: Optional[Decimal] = Decimal("0.00")
    min_stock_level: Optional[Decimal] = Decimal("0.00")
    max_stock_level: Optional[Decimal] = Decimal("0.00")
    primary_unit_id: int
    item_weight: Optional[Decimal] = None
    brand: Optional[int] = None
    barcode: Optional[str] = None
    item_images: Optional[str] = None 

class ItemUpdateSchema(Schema):
    item_code: str
    item_name: str = Field(..., min_length=1)
    category_id: int
    description: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    selling_price: Decimal = Decimal("0.00")
    tax: int
    hsn_code: Optional[str] = None
    opening_stock: Optional[Decimal] = None
    min_stock_level: Optional[Decimal] = None
    max_stock_level: Optional[Decimal] = None
    primary_unit_id: int
    item_weight: Optional[Decimal] = None
    brand: Optional[int] = None
    barcode: Optional[str] = None
    item_images: Optional[str] = None

    @field_validator('purchase_price', 'item_weight', 'selling_price', 'opening_stock', 'min_stock_level', 'max_stock_level', mode='before')
    @classmethod
    def empty_string_to_zero(cls, v: Any) -> Any:
        if v == "" or v is None:
            return Decimal("0.00")
        return v
