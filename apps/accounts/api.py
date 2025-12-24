from ninja import Router
from django.contrib.auth import get_user_model
from ninja.errors import HttpError
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
    MenuModuleMasterResponseSchema
)
from .auth_service import AuthService, ShopService
from .menu_service import MenuService, MenuModuleService
from apps.core.auth import BearerAuth

User = get_user_model()

auth_router = Router(tags=['Authentication'])

# ================================================================= ================================================================= =================================================================
# Authentication APIs
# ================================================================= ================================================================= =================================================================

# Send Otp for Signup
# @auth_router.post('/send-otp', response={200: OTPResponseSchema, 400: ErrorResponseSchema})
# def send_otp(request, payload: SendOTPSchema):
#     return AuthService.send_otp(payload.phone_number)

@auth_router.post('/send-otp', response={200: OTPResponseSchema, 400: ErrorResponseSchema})
def send_otp(request, payload: SendOTPSchema):
    try:
        data = AuthService.send_otp(payload.phone_number)
        return 200, {"success": True, "message": "Sent", "data": data}
    except Exception as e:
        return 400, {"success": False, "message": str(e), "data": None}

# Verify Otp
@auth_router.post('/verify-otp', response={200: SuccessResponseSchema, 400: ErrorResponseSchema})
def verify_otp(request, payload: VerifyOTPSchema):
    return AuthService.verify_otp(payload.dict())

# Register Shop
@auth_router.post('/register-shop', response={200: RegistrationResponseSchema, 400: ErrorResponseSchema})
def register_shop(request, payload: ShopRegistrationSchema):
    return ShopService.register_shop(request, payload)

# auth_router.post("/register-shop")(ShopService.register_shop)

# auth_router.post(
#     "/register-shop", 
#     response={201: RegistrationResponseSchema, 400: ErrorResponseSchema}
# )(ShopService.register_shop)


# Send OTP for Login
@auth_router.post('/send-login-otp', response={200: OTPResponseSchema, 400: ErrorResponseSchema})
def send_login_otp(request, payload: SendOTPSchema):
    return ShopService.send_login_otp(payload.phone_number)

# Login
@auth_router.post('/login', response={200: TokenResponseSchema, 400: ErrorResponseSchema})
def login(request, payload: LoginSchema):
    return ShopService.login(payload.phone_number, payload.email, payload.password, payload.otp_code)

# Logout
@auth_router.post('/logout', response={200: SuccessResponseSchema, 400: ErrorResponseSchema}, auth=BearerAuth())
def logout(request, payload: LogoutSchema):
    return ShopService.logout(payload.refresh)

# Session Data
@auth_router.get('/session-data', response={200: SessionDataSchema, 400: ErrorResponseSchema}, auth=BearerAuth())
def session_data(request):
    user = request.auth
    if not user:
        return {
            'success': False,
            'code': 400,
            'message': 'Authentication required',
            'data': None
        }
    return ShopService.get_session_data(user)


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