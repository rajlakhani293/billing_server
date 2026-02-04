from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Item, ItemCategory, ItemUnit


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ["id", 'item_code', 'item_name', 'category', 'primary_unit', 'current_stock', 'status', 'shop']
    list_filter = ['category', 'primary_unit', 'status', 'shop', 'brand']
    search_fields = ['item_code', 'item_name', 'brand', 'barcode']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('item_code', 'item_name', 'category', 'item_image', 'description', 'shop')
        }),
        ('Pricing Information', {
            'fields': ('purchase_price', 'selling_price')
        }),
        ('Tax Information', {
            'fields': ('tax_rate', 'hsn_code')
        }),
        ('Inventory Management', {
            'fields': ('opening_stock', 'current_stock', 'min_stock_level', 'max_stock_level')
        }),
        ('Units and Measurements', {
            'fields': ('primary_unit', 'item_weight')
        }),
        ('Additional Details', {
            'fields': ('brand', 'barcode')
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


@admin.register(ItemCategory)
class ItemCategoryAdmin(ModelAdmin):
    list_display = ["id", 'name', 'shop', 'status']
    list_filter = ['status', 'shop']
    search_fields = ['name', 'description']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'shop')
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


@admin.register(ItemUnit)
class ItemUnitAdmin(ModelAdmin):
    list_display = ["id", 'name', 'short_name', 'shop', 'status']
    list_filter = ['status', 'shop']
    search_fields = ['name', 'short_name']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'short_name', 'shop')
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
