from django.contrib import admin
from .models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['id','shop_code', 'shop_name', 'legal_name', 'phone_number', 'email', 'owner', 'default_shop', 'status', 'created_at']
    list_filter = ['default_shop', 'status', 'created_at', 'country', 'state']
    search_fields = ['shop_code', 'shop_name', 'legal_name', 'phone_number', 'email', 'tax_no', 'pan_no']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Info', {'fields': ('id','shop_code', 'shop_name', 'legal_name', 'owner')}),
        ('Contact Info', {'fields': ('phone_number', 'email')}),
        ('Tax Info', {'fields': ('tax_no', 'pan_no')}),
        ('Address Info', {'fields': ('address', 'pincode', 'country', 'state', 'city')}),
        ('Settings', {'fields': ('default_shop', 'status', 'logo_image')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
