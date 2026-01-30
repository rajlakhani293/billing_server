from ninja import Schema
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

class ItemCreateSchema(Schema):
    item_name: str
    primary_unit: int
    description: Optional[str] = None
    purchase_price: Optional[Decimal] = 0.00
    selling_price: Optional[Decimal] = 0.00
    tax_rate: Optional[Decimal] = 0.00
    hsn_code: Optional[str] = None
    opening_stock: Optional[Decimal] = 0.00
    min_stock_level: Optional[Decimal] = 0.00
    max_stock_level: Optional[Decimal] = 0.00
    item_weight: Optional[Decimal] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    status: Optional[int] = 0
