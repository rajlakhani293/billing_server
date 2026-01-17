from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI
from ninja.errors import ValidationError
from apps.accounts.api import auth_router
from apps.core.api import location_router
from apps.core.helpers import validation_error_handler
from apps.parties.api import parties_router

# Initialize Ninja API
api = NinjaAPI(
    title='Billing Server API',
    version='1.0.0',
    description='API for retail billing software'
)

api.add_exception_handler(ValidationError, validation_error_handler)

# Add routers
api.add_router('/auth', auth_router)
api.add_router('/parties', parties_router)
api.add_router('/locations', location_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api.urls),
]

# Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
