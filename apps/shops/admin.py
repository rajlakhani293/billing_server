from django.contrib import admin
from .models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['id','shop_code', 'shop_name', 'legal_name', 'phone_number', 'email', 'owner', 'default_shop', 'status', 'created_at']
    list_filter = ['default_shop', 'status', 'created_at', 'country', 'state']
    search_fields = ['shop_code', 'shop_name', 'legal_name', 'phone_number', 'email', 'tax_no', 'pan_no']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def has_add_permission(self, request):
        # Superusers and shop owners can add shops
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())

    def has_view_permission(self, request, obj=None):
        # Superusers and shop owners can view shops
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())

    def has_module_permission(self, request):
        # Superusers and shop owners can see the module
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusers see all shops
        if request.user.is_superuser:
            return qs
        # Shop owners only see their own shops
        elif request.user.is_staff and request.user.shops.exists():
            return qs.filter(id__in=request.user.shops.all())
        return qs.none()

    def has_change_permission(self, request, obj=None):
        # Superusers can change everything
        if request.user.is_superuser:
            return True
        # Shop owners can only edit their own shops
        if request.user.is_staff and request.user.shops.exists() and obj:
            return obj.id in [shop.id for shop in request.user.shops.all()]
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Superusers can delete everything
        if request.user.is_superuser:
            return True
        # Shop owners can only delete their own shops (but not their primary shop)
        if request.user.is_staff and request.user.shops.exists() and obj:
            return obj.id in [shop.id for shop in request.user.shops.all()] and obj.id != request.user.primary_shop.id
        return super().has_delete_permission(request, obj)

    fieldsets = (
        ('Basic Info', {'fields': ('id','shop_code', 'shop_name', 'legal_name', 'owner')}),
        ('Contact Info', {'fields': ('phone_number', 'email')}),
        ('Tax Info', {'fields': ('tax_no', 'pan_no')}),
        ('Address Info', {'fields': ('address', 'pincode', 'country', 'state', 'city')}),
        ('Settings', {'fields': ('default_shop', 'status', 'logo_image')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
