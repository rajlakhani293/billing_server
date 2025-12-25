from ninja import Router
from django.contrib.auth import get_user_model
from .schema import (
    SendOTPSchema,
    VerifyOTPSchema,
    ShopRegistrationSchema,
    LoginSchema,
    LogoutSchema,
    OTPResponseSchema,
    RegistrationResponseSchema,
    TokenResponseSchema,
    SuccessResponseSchema,
    ErrorResponseSchema,
    SessionDataSchema,
    MenuMasterCreateSchema,
    MenuMasterUpdateSchema,
    MenuMasterResponseSchema,
    MenuModuleMasterCreateSchema,
    MenuModuleMasterUpdateSchema,
    MenuModuleMasterResponseSchema,
    ResetOTPSchema,
    BlockedUsersResponseSchema,
    ResetOTPResponseSchema
)
from .auth_service import AuthService, OTPLimitService
from .menu_service import MenuService, MenuModuleService
from apps.core.auth import AuthBearer

User = get_user_model()

auth_router = Router(tags=['Authentication'])

# ================================================================= ================================================================= =================================================================
# Authentication APIs
# ================================================================= ================================================================= =================================================================

# Send Otp for Signup
@auth_router.post('/send-otp', response={200: OTPResponseSchema, 400: ErrorResponseSchema})
def send_otp(request, payload: SendOTPSchema):
    result = AuthService.send_otp(payload.phone_number)
    
    if result['success']:
        return 200, result
    else:
        return 400, result

# Verify Otp
@auth_router.post('/verify-otp', response={200: SuccessResponseSchema, 400: ErrorResponseSchema})
def verify_otp(request, payload: VerifyOTPSchema):
    result = AuthService.verify_otp(payload.dict())
    
    if result['success']:
        return 200, result
    else:
        return 400, result

# Register Shop
@auth_router.post('/register-shop', response={200: RegistrationResponseSchema, 400: ErrorResponseSchema})
def register_shop(request, payload: ShopRegistrationSchema):
    result = AuthService.register_shop(request, payload)
    
    if result['success']:
        return 200, result
    else:
        return 400, result

# Send OTP for Login
@auth_router.post('/send-login-otp', response={200: OTPResponseSchema, 400: ErrorResponseSchema})
def send_login_otp(request, payload: SendOTPSchema):
    result = AuthService.send_login_otp(payload.phone_number)
    
    if result['success']:
        return 200, result
    else:
        return 400, result

# Login
@auth_router.post('/login', response={200: TokenResponseSchema, 400: ErrorResponseSchema})
def login(request, payload: LoginSchema):
    result = AuthService.login(payload.dict())
    
    if result['success']:
        return 200, result
    else:
        return 400, result

# Logout
@auth_router.post('/logout', response={200: SuccessResponseSchema, 400: ErrorResponseSchema}, auth=AuthBearer())
def logout(request, payload: LogoutSchema):
    return AuthService.logout(payload.refresh)

# Session Data
@auth_router.get('/session-data', response={200: SessionDataSchema, 400: ErrorResponseSchema}, auth=AuthBearer())
def session_data(request):
    user = request.auth 
    return AuthService.get_session_data(user)


# ================================================================= ================================================================= =================================================================
# OTP Limit Management APIs
# ================================================================= ================================================================= =================================================================

# Get all users with OTP limit reached (blocked users)
@auth_router.get('/blocked-users', response={200: BlockedUsersResponseSchema, 400: ErrorResponseSchema})
def get_blocked_users(request):
    return OTPLimitService.get_blocked_users()

# Reset OTP timer for a specific user
@auth_router.post('/reset-otp-limit', response={200: ResetOTPResponseSchema, 400: ErrorResponseSchema, 404: ErrorResponseSchema})
def reset_otp_limit(request, payload: ResetOTPSchema):
    return OTPLimitService.reset_otp_limit(payload.phone_number)


# ================================================================= ================================================================= =================================================================
# Menu Master APIs 
# ================================================================= ================================================================= =================================================================

menu_master_router = Router(tags=['Menu Master'])

# Create Menu Master
@menu_master_router.post('/', response={201: MenuMasterResponseSchema, 400: ErrorResponseSchema})
def create(request, payload: MenuMasterCreateSchema):
    return MenuService.create(payload.dict())

# Get all Menu Masters
@menu_master_router.get('/get-transactions', response={200: dict, 400: ErrorResponseSchema})
def getAll(request):
    return MenuService.getAll()

# Get Menu Master by ID
@menu_master_router.get('/{menu_id}', response={200: MenuMasterResponseSchema, 400: ErrorResponseSchema, 404: ErrorResponseSchema})
def getById(request, menu_id: str):
    return MenuService.getById(menu_id)

# Update Menu Master
@menu_master_router.put('/{menu_id}', response={200: MenuMasterResponseSchema, 400: ErrorResponseSchema, 404: ErrorResponseSchema})
def update(request, menu_id: str, payload: MenuMasterUpdateSchema):
    return MenuService.update(menu_id, payload.dict())

# Delete Menu Master
@menu_master_router.delete('/{menu_id}', response={200: SuccessResponseSchema, 400: ErrorResponseSchema, 404: ErrorResponseSchema})
def delete(request, menu_id: str):
    return MenuService.delete(menu_id)


# ================================================================= ================================================================= =================================================================
# Menu Module Master API
# ================================================================= ================================================================= =================================================================

menu_module_router = Router(tags=['Menu Module Master'])

# Get all Menu Module Masters
@menu_module_router.get('/get-transactions', response={200: dict, 400: ErrorResponseSchema})
def getAll(request):
    return MenuModuleService.getAll()

# Get Menu Module Master by ID
@menu_module_router.get('/{module_id}', response={200: MenuModuleMasterResponseSchema, 400: ErrorResponseSchema, 404: ErrorResponseSchema})
def getById(request, module_id: str):
    return MenuModuleService.getById(module_id)

# Create Menu Module Master
@menu_module_router.post('/', response={201: MenuModuleMasterResponseSchema, 400: ErrorResponseSchema})
def create(request, payload: MenuModuleMasterCreateSchema):
    return MenuModuleService.create(payload.dict())

# Update Menu Module Master
@menu_module_router.put('/{module_id}', response={200: MenuModuleMasterResponseSchema, 400: ErrorResponseSchema, 404: ErrorResponseSchema})
def update(request, module_id: str, payload: MenuModuleMasterUpdateSchema):
    return MenuModuleService.update(module_id, payload.dict())

# Delete Menu Module Master
@menu_module_router.delete('/{module_id}', response={200: SuccessResponseSchema, 400: ErrorResponseSchema, 404: ErrorResponseSchema})
def delete(request, module_id: str):
    return MenuModuleService.delete(module_id)