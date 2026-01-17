from ninja import ModelSchema, Schema
from typing import Optional
from datetime import datetime
from apps.shops.models import Shop


# Request Schemas
class SendOTPSchema(Schema):
    phone_number: str


class VerifyOTPSchema(Schema):
    phone_number: str
    otp_code: str

class ShopRegistrationSchema(ModelSchema):
    class Config:
        model = Shop
        fields = "__all__"

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


