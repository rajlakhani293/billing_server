from ninja import Schema, Form
from ninja.files import UploadedFile
from typing import Optional

# ================================================================= ================================================================= =================================================================
# Company Schemas
# ================================================================= ================================================================= =================================================================

class CompanyUpdateSchema(Schema):
    company_name: str
    business_type_id: Optional[int] = None
    phone_number: str
    email: Optional[str] = None
    tax_no: Optional[str] = None
    pan_no: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    country: int
    state: int
    city: int
    website_url: Optional[str] = None
    logo_image: Optional[str] = None


# ================================================================= ================================================================= =================================================================
# Branch Schemas
# ================================================================= ================================================================= =================================================================

class BranchCreateSchema(Schema):
    branch_name: str
    pincode: Optional[int] = None
    country_id: int
    state_id: int
    city_id: int

class BranchUpdateSchema(Schema):
    branch_name: str
    pincode: Optional[int] = None
    country_id: int
    state_id: int
    city_id: int