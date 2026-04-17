from ninja import Schema, Form
from ninja.files import UploadedFile
from typing import Optional

# ================================================================= ================================================================= =================================================================
# Company Schemas
# ================================================================= ================================================================= =================================================================

class CompanyUpdateSchema(Schema):
    company_name: Optional[str] = None
    business_type_id: Optional[int] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    tax_no: Optional[str] = None
    pan_no: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[int] = None
    state: Optional[int] = None
    city: Optional[int] = None
    website_url: Optional[str] = None
    status: Optional[int] = None

class CompanyCreateSchema(Schema):
    company_name: str
    business_type_id: Optional[int] = 0
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

# ================================================================= ================================================================= =================================================================
# Branch Schemas
# ================================================================= ================================================================= =================================================================

class BranchCreateSchema(Schema):
    branch_name: str
    contact_person_name: str
    phone_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    country: int
    state: int
    city: int
    company: int

class BranchUpdateSchema(Schema):
    branch_name: Optional[str] = None
    contact_person_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[int] = None
    state: Optional[int] = None
    city: Optional[int] = None
    status: Optional[int] = None
