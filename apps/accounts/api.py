from ninja import Router
from django.contrib.auth import get_user_model
from .schema import (
    SendOTPSchema,
    SessionDataRequestSchema,
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
from .helpers import handle_response, handle_not_found_response
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
    return handle_response(result)

# Verify Otp
@auth_router.post('/verify-otp', response={200: SuccessResponseSchema, 400: ErrorResponseSchema})
def verify_otp(request, payload: VerifyOTPSchema):
    result = AuthService.verify_otp(payload.dict())
    return handle_response(result)

# Register Shop
@auth_router.post('/register-shop', response={200: RegistrationResponseSchema, 400: ErrorResponseSchema})
def register_shop(request, payload: ShopRegistrationSchema):
    result = AuthService.register_shop(request, payload)
    return handle_response(result)

# Send OTP for Login
@auth_router.post('/send-login-otp', response={200: OTPResponseSchema, 400: ErrorResponseSchema})
def send_login_otp(request, payload: SendOTPSchema):
    result = AuthService.send_login_otp(payload.phone_number)
    return handle_response(result)

# Login
@auth_router.post('/login', response={200: TokenResponseSchema, 400: ErrorResponseSchema})
def login(request, payload: LoginSchema):
    result = AuthService.login(payload.dict())
    return handle_response(result)

# Logout
@auth_router.post('/logout', response={200: SuccessResponseSchema, 400: ErrorResponseSchema}, auth=AuthBearer())
def logout(request, payload: LogoutSchema):
    result = AuthService.logout(payload.refresh)
    return handle_response(result)

# Session Data
@auth_router.post('/session-data', response={200: SessionDataSchema, 400: ErrorResponseSchema}, auth=AuthBearer())
def session_data(request, payload: SessionDataRequestSchema):
    result = AuthService.get_session_data(payload.dict())
    return handle_response(result)


# ================================================================= ================================================================= =================================================================
# OTP Limit Management APIs
# ================================================================= ================================================================= =================================================================

# Get all users with OTP limit reached (blocked users)
@auth_router.get('/blocked-users', response={200: BlockedUsersResponseSchema, 400: ErrorResponseSchema})
def get_blocked_users(request):
    result = OTPLimitService.get_blocked_users()
    return handle_response(result)

# Reset OTP timer for a specific user
@auth_router.post('/reset-otp-limit', response={200: ResetOTPResponseSchema, 400: ErrorResponseSchema})
def reset_otp_limit(request, payload: ResetOTPSchema):
    result = OTPLimitService.reset_otp_limit(payload.phone_number)
    return handle_response(result)


# ================================================================= ================================================================= =================================================================
# Menu Master APIs 
# ================================================================= ================================================================= =================================================================

menu_master_router = Router(tags=['Menu Master'])

# Create Menu Master
@menu_master_router.post('/', response={200: MenuMasterResponseSchema, 400: ErrorResponseSchema})
def create(request, payload: MenuMasterCreateSchema):
    result = MenuService.create(payload.dict())
    return handle_response(result)
    

# Get all Menu Masters
@menu_master_router.get('/get-transactions', response={200: dict, 400: ErrorResponseSchema})
def getAll(request):
    result = MenuService.getAll()
    return handle_response(result)

# Get Menu Master by ID
@menu_master_router.get('/{menu_id}', response={200: MenuMasterResponseSchema, 400: ErrorResponseSchema})
def getById(request, menu_id: str):
    result = MenuService.getById(menu_id)
    return handle_not_found_response(result, "Menu not found")

# Update Menu Master
@menu_master_router.put('/{menu_id}', response={200: MenuMasterResponseSchema, 400: ErrorResponseSchema})
def update(request, menu_id: str, payload: MenuMasterUpdateSchema):
    payload_dict = payload.dict()
    payload_dict['id'] = menu_id
    result = MenuService.update(payload_dict)
    return handle_not_found_response(result, "Menu not found")

# Delete Menu Master
@menu_master_router.delete('/{menu_id}', response={200: SuccessResponseSchema, 400: ErrorResponseSchema})
def delete(request, menu_id: str):
    result = MenuService.delete(menu_id)
    return handle_not_found_response(result, "Menu not found")


# ================================================================= ================================================================= =================================================================
# Menu Module Master API
# ================================================================= ================================================================= =================================================================

menu_module_router = Router(tags=['Menu Module Master'])

# Create Menu Module Master
@menu_module_router.post('/', response={200: MenuModuleMasterResponseSchema, 400: ErrorResponseSchema})
def create(request, payload: MenuModuleMasterCreateSchema):
    result = MenuModuleService.create(payload.dict())
    return handle_response(result)

# Get all Menu Module Masters
@menu_module_router.get('/get-transactions', response={200: dict, 400: ErrorResponseSchema})
def getAll(request):
    result = MenuModuleService.getAll()
    return handle_response(result)

# Get Menu Module Master by ID
@menu_module_router.get('/{module_id}', response={200: MenuModuleMasterResponseSchema, 400: ErrorResponseSchema})
def getById(request, module_id: str):
    result = MenuModuleService.getById(module_id)
    return handle_not_found_response(result, "Menu module not found")

# Update Menu Module Master
@menu_module_router.put('/{module_id}', response={200: MenuModuleMasterResponseSchema, 400: ErrorResponseSchema})
def update(request, module_id: str, payload: MenuModuleMasterUpdateSchema):
    # Add the id to payload for the service method
    payload_dict = payload.dict()
    payload_dict['id'] = module_id
    result = MenuModuleService.update(payload_dict)
    return handle_not_found_response(result, "Menu module not found")

# Delete Menu Module Master
@menu_module_router.delete('/{module_id}', response={200: SuccessResponseSchema, 400: ErrorResponseSchema})
def delete(request, module_id: str):
    result = MenuModuleService.delete(module_id)
    return handle_not_found_response(result, "Menu module not found")