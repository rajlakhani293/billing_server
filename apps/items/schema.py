from ninja import Schema
from typing import Optional
from decimal import Decimal

class ItemDropdownSchema(Schema):
    id: int
    item_name: str
    item_code: str
    current_stock: Decimal
    selling_price: Decimal
    
    class Config:
        from_attributes = True

class ItemStatusUpdateSchema(Schema):
    id: int
    status: int
