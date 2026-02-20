from ninja import Router
from django.contrib.auth import get_user_model
from .schema import (
    SendOTPSchema,
    VerifyOTPSchema,
    ShopRegistrationSchema,
    LoginSchema,
    LogoutSchema,
    ResetOTPSchema,
)
from .auth_service import AuthService, OTPLimitService
from apps.core.auth import AuthBearer

User = get_user_model()

auth_router = Router(tags=['Authentication'])

# ================================================================= ================================================================= =================================================================
# Authentication APIs
# ================================================================= ================================================================= =================================================================

# Send Otp for Signup
@auth_router.post('/send-otp')
def send_otp(request, payload: SendOTPSchema):
    return AuthService.send_otp(payload.phone_number)

# Verify Otp
@auth_router.post('/verify-otp')
def verify_otp(request, payload: VerifyOTPSchema):
    return AuthService.verify_otp(payload.dict())

# Register Shop
@auth_router.post('/register-shop')
def register_shop(request, payload: ShopRegistrationSchema):
    return AuthService.register_shop(payload)

# Send OTP for Login
@auth_router.post('/send-login-otp')
def send_login_otp(request, payload: SendOTPSchema):
    return AuthService.send_login_otp(payload.phone_number)

# Login
@auth_router.post('/login')
def login(request, payload: LoginSchema):
    return AuthService.login(payload.dict())

# Logout
@auth_router.post('/logout', auth=AuthBearer())
def logout(request, payload: LogoutSchema):
    return AuthService.logout(payload.refresh)

# ================================================================= ================================================================= =================================================================
# OTP Limit Management APIs
# ================================================================= ================================================================= =================================================================

# Get all users with OTP limit reached (blocked users)
@auth_router.get('/blocked-users')
def get_blocked_users(request):
    return OTPLimitService.get_blocked_users()

# Reset OTP timer for a specific user
@auth_router.post('/reset-otp-limit')
def reset_otp_limit(request, payload: ResetOTPSchema):
    return OTPLimitService.reset_otp_limit(payload.phone_number)
