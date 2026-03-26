from ninja import Schema
from typing import Optional

# Request Schemas
class SendOTPSchema(Schema):
    phone_number: str

class VerifyOTPSchema(Schema):
    phone_number: str
    otp_code: str

class CompanyRegistrationSchema(Schema):
    # Registration Info
    registration_token: str
    
    # User Info (for User model)
    user_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    # Company Info (matching Company model)
    company_name: str
    legal_name: Optional[str] = None
    business_type_id: Optional[int] = 0
    phone_number: str
    tax_no: Optional[str] = None
    pan_no: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    country: int
    state: int
    city: int
    logo_image: Optional[str] = None
    website_url: Optional[str] = None

class LoginSchema(Schema):
    phone_number: Optional[str] = None
    otp_code: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class LogoutSchema(Schema):
    refresh: str

# OTP Limit Management Schemas
class ResetOTPSchema(Schema):
    phone_number: str



