from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Party


@admin.register(Party)
class PartyAdmin(ModelAdmin):
    list_display = ["id",'name', 'party_type', 'phone_number', 'email', 'wallet_balance', 'balance_type', 'customer_category', 'status', 'shop']
    list_filter = ['party_type', 'customer_category', 'balance_type', 'status', 'shop', 'city', 'state', 'country']
    search_fields = ['name', 'phone_number', 'email']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'party_type', 'customer_category', 'shop')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'address', 'city', 'state', 'country', 'pincode')
        }),
        ('Financial Information', {
            'fields': ('wallet_balance', 'balance_type')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            # 'classes': ('collapse',)
        }),
    )
    
    def has_module_permission(self, request):
        # Superusers and shop owners can see the parties module
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('shop', 'city', 'state', 'country')
        
        # If user is superuser, show all parties
        if request.user.is_superuser:
            return qs
        
        # If user is not superuser, only show parties from their shops (filter by shop IDs)
        if hasattr(request.user, 'shops') and request.user.shops.exists():
            user_shop_ids = request.user.shops.values_list('id', flat=True)
            return qs.filter(shop_id__in=user_shop_ids)
        
        # If user has no shops assigned, return empty queryset
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # If user is not superuser, limit shop choices to their shops
        if not request.user.is_superuser and hasattr(request.user, 'shops'):
            form.base_fields['shop'].queryset = request.user.shops.all()
        
        return form
    
    def has_view_permission(self, request, obj=None):
        # Superuser can view all, others can only view if they have shop access
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop_id in user_shop_ids
    
    def has_change_permission(self, request, obj=None):
        # Superuser can change all, others can only change if they have shop access
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop_id in user_shop_ids
    
    def has_delete_permission(self, request, obj=None):
        # Superuser can delete all, others can only delete if they have shop access
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'shops') and request.user.shops.exists()
        user_shop_ids = request.user.shops.values_list('id', flat=True)
        return obj.shop_id in user_shop_ids
    
    def has_add_permission(self, request):
        # Superuser can add to any shop, others can add only if they have shops
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'shops') and request.user.shops.exists()
