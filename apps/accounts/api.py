from ninja import Router, Form, File
from ninja.files import UploadedFile
from .schema import (
    SendOTPSchema,
    VerifyOTPSchema,
    CompanyRegistrationSchema,
    LoginSchema,
    LogoutSchema,
    ResetOTPSchema,
)
from .auth_service import AuthService, OTPLimitService
from apps.core.auth import AuthBearer


auth_router = Router(tags=['Authentication'])

# ================================================================= ================================================================= =================================================================
# Authentication APIs
# ================================================================= ================================================================= =================================================================

# Send Otp for Signup
@auth_router.post('/send-otp')
def send_otp(request, payload: SendOTPSchema):
    return AuthService.sendOtp(payload.phone_number)

# Verify Otp
@auth_router.post('/verify-otp')
def verify_otp(request, payload: VerifyOTPSchema):
    return AuthService.verifyOtp(payload.dict())

# Register Company
@auth_router.post('/register-company')
def register_company(request, payload: CompanyRegistrationSchema = Form(...), logo_image: UploadedFile = File(None)):
    data = payload.dict()
    if logo_image:
        data["logo_image"] = logo_image
    return AuthService.registerCompany(data)

# Send OTP for Login
@auth_router.post('/send-login-otp')
def send_login_otp(request, payload: SendOTPSchema):
    return AuthService.sendLoginOtp(payload.phone_number)

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

@auth_router.get('/blocked-users')
def get_blocked_users(request):
    return OTPLimitService.getBlockedUsers(request)

@auth_router.post('/reset-otp-limit')
def reset_otp_limit(request, payload: ResetOTPSchema):
    return OTPLimitService.resetOtpLimit(payload.phone_number, request)
