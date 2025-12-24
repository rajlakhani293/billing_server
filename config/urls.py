from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI
from apps.accounts.api import auth_router, menu_master_router, menu_module_router
from apps.core.api import location_router

# Initialize Ninja API
api = NinjaAPI(
    title='Billing Server API',
    version='1.0.0',
    description='API for retail billing software'
)

# Add routers
api.add_router('/auth', auth_router)
api.add_router('/locations', location_router)
api.add_router('/menu-master', menu_master_router)
api.add_router('/module-master', menu_module_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api.urls),
]

# Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
