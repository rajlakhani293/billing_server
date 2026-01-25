from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Sales, SalesTransaction


class SalesTransactionInline(TabularInline):
    model = SalesTransaction
    extra = 1
    readonly_fields = ['tax_amount', 'discount_amount']
    fields = ['item', 'item_quantity', 'item_rate', 'discount_percentage']


@admin.register(Sales)
class SalesAdmin(ModelAdmin):
    list_display = ["id", 'sales_code', 'party', 'shop', 'total_amount', 'paid_amount', 'payment_mode', 'sales_date', 'status']
    list_filter = ['payment_mode', 'sales_date', 'shop', 'party']
    search_fields = ['sales_code', 'party__name', 'notes']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SalesTransactionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('sales_code', 'party', 'shop', 'sales_date')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'discount_percentage', 'discount_amount', 'total_amount', 'paid_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_mode',)
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def has_module_permission(self, request):
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('party', 'shop')
        
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
            form.base_fields['party'].queryset = Party.objects.filter(shop__in=request.user.shops.all())
        
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
