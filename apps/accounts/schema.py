from ninja import Schema
from typing import Optional
from datetime import datetime


# Request Schemas
class SendOTPSchema(Schema):
    phone_number: str


class VerifyOTPSchema(Schema):
    phone_number: str
    otp_code: str


class ShopRegistrationSchema(Schema):
    # Registration Info
    registration_token: str
    
    # User Info (for User model)
    user_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    # Shop Info (matching Shop model)
    shop_name: str
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

class SessionDataRequestSchema(Schema):
    user_id: int
    shop_id: int


# Response Schemas
class BaseResponseSchema(Schema):
    success: bool
    code: int
    message: str


class OTPDataSchema(Schema):
    otp_code: str


class OTPResponseSchema(BaseResponseSchema):
    data: OTPDataSchema


class TokenDataSchema(Schema):
    access: str
    refresh: str
    user_id: int
    phone_number: str
    email: Optional[str] = None
    has_password: bool


class TokenResponseSchema(BaseResponseSchema):
    data: TokenDataSchema


class UserDataSchema(Schema):
    id: int
    phone_number: str
    email: Optional[str] = None
    user_name: Optional[str] = None
    is_verified: bool
    is_staff: bool
    has_password: bool
    role: Optional[str] = None


class UserResponseSchema(BaseResponseSchema):
    data: UserDataSchema


class ShopDataSchema(Schema):
    id: int
    shop_code: Optional[str] = None
    shop_name: str
    legal_name: Optional[str] = None
    business_type_id: Optional[int] = 0
    email: Optional[str] = None
    phone_number: Optional[str] = None
    tax_no: Optional[str] = None
    pan_no: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[int] = None
    state: Optional[int] = None
    country: Optional[int] = None
    logo_image: Optional[str] = None
    website_url: Optional[str] = None
    default_shop: int
    status: int
    created_at: datetime


class ShopResponseSchema(BaseResponseSchema):
    data: ShopDataSchema


class RegistrationDataSchema(Schema):
    user: Optional[UserDataSchema] = None
    shop: Optional[ShopDataSchema] = None
    tokens: Optional[TokenDataSchema] = None


class RegistrationResponseSchema(BaseResponseSchema):
    data: RegistrationDataSchema


class ErrorDataSchema(Schema):
    details: Optional[dict] = None
    field_errors: Optional[dict] = None


class ErrorResponseSchema(BaseResponseSchema):
    success: bool = False
    data: Optional[ErrorDataSchema] = None


class SuccessResponseSchema(BaseResponseSchema):
    data: Optional[dict] = None


class SessionDataSchema(BaseResponseSchema):
    data: dict


# Menu Master Schemas
class MenuMasterCreateSchema(Schema):
    menu_name: str
    cust_menu_name: str
    priority: int = 0
    menu_icon_name: Optional[str] = None
    menu_url: Optional[str] = None
    status: int = 0


class MenuMasterUpdateSchema(Schema):
    menu_name: str
    cust_menu_name: str
    priority: Optional[int] = None
    menu_icon_name: Optional[str] = None
    menu_url: str

class MenuMasterDataSchema(Schema):
    id: int
    menu_name: str
    cust_menu_name: str
    priority: int
    menu_icon_name: Optional[str] = None
    menu_url: Optional[str] = None
    status: int


class MenuMasterResponseSchema(BaseResponseSchema):
    data: MenuMasterDataSchema


class MenuModuleMasterDataSchema(Schema):
    id: int
    menu: Optional[MenuMasterDataSchema] = None
    module_name: str
    cust_module_name: str
    module_url: str
    module_description: Optional[str] = None
    module_permission_type_ids: str
    priority: int
    module_icon_name: Optional[str] = None
    module_visibility: int
    status: int


class MenuModuleMasterResponseSchema(BaseResponseSchema):
    data: MenuModuleMasterDataSchema


# Menu Module Master Schemas
class MenuModuleMasterCreateSchema(Schema):
    menu: str
    module_name: str
    cust_module_name: str
    module_url: str
    module_description: Optional[str] = None
    module_permission_type_ids: str
    priority: int
    module_icon_name: Optional[str] = None
    module_visibility: int = 1


class MenuModuleMasterUpdateSchema(Schema):
    menu: str
    module_name: str
    cust_module_name: str
    module_url: str
    module_description: Optional[str] = None
    module_permission_type_ids: str
    priority: Optional[int] = None
    module_icon_name: Optional[str] = None
    module_visibility: Optional[int] = None


class MenuModuleMasterResponseSchema(BaseResponseSchema):
    data: dict


# OTP Limit Management Schemas
class ResetOTPSchema(Schema):
    phone_number: str


class BlockedUserDataSchema(Schema):
    phone_number: str
    user_name: Optional[str] = None
    email: Optional[str] = None
    blocked_until: datetime
    remaining_minutes: int
    otp_attempts: int


class BlockedUsersResponseSchema(BaseResponseSchema):
    data: list[BlockedUserDataSchema]


class ResetOTPResponseSchema(BaseResponseSchema):
    data: Optional[dict] = None
