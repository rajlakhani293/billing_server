from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Brand, Tax, Party


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ["id", 'brand_name', 'shop', 'status']
    list_filter = ['status', 'shop']
    search_fields = ['brand_name']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('brand_name', 'shop')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def has_module_permission(self, request):
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('shop')
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'shops') and request.user.shops.exists():
            user_shop_ids = request.user.shops.values_list('id', flat=True)
            return qs.filter(shop__in=user_shop_ids)
        
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser and hasattr(request.user, 'shops'):
            form.base_fields['shop'].queryset = request.user.shops.all()
        
        return form
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop.id in user_shop_ids
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop.id in user_shop_ids
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop.id in user_shop_ids
    
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'shops') and request.user.shops.exists()


@admin.register(Tax)
class TaxAdmin(ModelAdmin):
    list_display = ["id", 'tax_name', 'tax_value', 'shop', 'status']
    list_filter = ['status', 'shop']
    search_fields = ['tax_name']
    list_editable = ['status', 'tax_value']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tax_name', 'tax_value', 'shop')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def has_module_permission(self, request):
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('shop')
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'shops') and request.user.shops.exists():
            user_shop_ids = request.user.shops.values_list('id', flat=True)
            return qs.filter(shop__in=user_shop_ids)
        
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser and hasattr(request.user, 'shops'):
            form.base_fields['shop'].queryset = request.user.shops.all()
        
        return form
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop.id in user_shop_ids
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop.id in user_shop_ids
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop.id in user_shop_ids
    
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'shops') and request.user.shops.exists()


@admin.register(Party)
class PartyAdmin(ModelAdmin):
    list_display = ["id", 'name', 'party_type', 'phone_number', 'shop', 'status']
    list_filter = ['party_type', 'status', 'shop']
    search_fields = ['name', 'phone_number', 'email']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'wallet_balance']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'party_type', 'phone_number', 'email', 'shop')
        }),
        ('Address Details', {
            'fields': ('address', 'city', 'state', 'country', 'pincode')
        }),
        ('Financial Info', {
            'fields': ('wallet_balance', 'balance_type', 'customer_category')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def has_module_permission(self, request):
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('shop', 'city', 'state', 'country')
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'shops') and request.user.shops.exists():
            user_shop_ids = request.user.shops.values_list('id', flat=True)
            return qs.filter(shop__in=user_shop_ids)
        
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser and hasattr(request.user, 'shops'):
            form.base_fields['shop'].queryset = request.user.shops.all()
        
        return form
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop.id in user_shop_ids
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop.id in user_shop_ids
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop.id in user_shop_ids
    
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'shops') and request.user.shops.exists()
