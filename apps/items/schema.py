from ninja import Field, Schema
from typing import Optional, Union
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
    purchase_price: Optional[Union[str, Decimal]] = None
    selling_price: Decimal = Decimal("0.00")
    opening_stock: Optional[Union[str, Decimal]] = Decimal("0.00")
    min_stock_level: Optional[Union[str, Decimal]] = Decimal("0.00")
    primary_unit_id: int
    item_weight: Optional[Union[str, Decimal]] = None
    brand: Optional[Union[str, int]] = None
    barcode: Optional[str] = None
    item_images: Optional[str] = None

    @field_validator('purchase_price', 'item_weight', 'barcode', mode='before')
    @classmethod
    def validate_decimal_fields(cls, v):
        if v == "" or v is None:
            return None
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Value must be a valid decimal number")

    @field_validator('opening_stock', 'min_stock_level', mode='before')
    @classmethod
    def validate_stock_fields(cls, v):
        if v == "" or v is None:
            return Decimal("0.00")
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Value must be a valid decimal number")

    @field_validator('brand', mode='before')
    @classmethod
    def validate_brand(cls, v):
        if v == "" or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError("Brand must be a valid integer")

class ItemUpdateSchema(Schema):
    item_code: str
    item_name: str = Field(..., min_length=1)
    category_id: int
    description: Optional[str] = None
    purchase_price: Optional[Union[str, Decimal]] = None
    selling_price: Decimal = Decimal("0.00")
    min_stock_level: Optional[Union[str, Decimal]] = Decimal("0.00")
    primary_unit_id: int
    item_weight: Optional[Union[str, Decimal]] = None
    brand: Optional[Union[str, int]] = None
    barcode: Optional[str] = None
    item_images: Optional[str] = None

    @field_validator('purchase_price', 'item_weight', 'barcode', mode='before')
    @classmethod
    def validate_decimal_fields(cls, v):
        if v == "" or v is None:
            return None
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Value must be a valid decimal number")

    @field_validator('min_stock_level', mode='before')
    @classmethod
    def validate_stock_fields(cls, v):
        if v == "" or v is None:
            return Decimal("0.00")
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Value must be a valid decimal number")

    @field_validator('brand', mode='before')
    @classmethod
    def validate_brand(cls, v):
        if v == "" or v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError("Brand must be a valid integer")


class StockAdjustmentIn(Schema):
    item_id: int
    movement_type: str
    quantity: Union[str, Decimal]
    note: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None

    @field_validator('quantity', mode='before')
    @classmethod
    def validate_quantity(cls, v):
        try:
            qty = Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Quantity must be a valid decimal number")

        if qty <= 0:
            raise ValueError("Quantity must be greater than 0")

        return qty
