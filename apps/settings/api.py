
from ninja.router import Router
from apps.accounts.auth_service import AuthService
from apps.core.auth import AuthBearer


setting_router = Router(tags=['Setting'])

# Session Data
@setting_router.get('/session-data', auth=AuthBearer())
def session_data(request):
    return AuthService.get_session_data(request)