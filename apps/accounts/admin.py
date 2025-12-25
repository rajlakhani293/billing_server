from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, RolePermission, MenuMaster, MenuModuleMaster


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["id",'phone_number', 'user_name', 'email', 'is_verified', 'is_active', 'is_staff', 'user_lock', 'status', 'created_at']
    list_filter = ['is_verified', 'is_active', 'is_staff', 'user_lock', 'status', 'created_at']
    search_fields = ['phone_number', 'email', 'user_name']
    ordering = ['-created_at']
    filter_horizontal = ['shops', 'groups', 'user_permissions']

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('email', 'user_name')}),
        ('Address Info', {'fields': ('address', 'country', 'state', 'city', 'pincode')}),
        ('Shop Info', {'fields': ('role', 'shops', 'primary_shop', 'permissions')}),
        ('Permissions', {'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser', 'user_lock', 'status', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'email', 'user_name', 'is_verified'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'otp_code', 'otp_type', 'is_verified', 'attempts', 'blocked_until', 'created_at']
    list_filter = ['otp_type', 'is_verified', 'created_at']
    search_fields = ['phone_number', 'otp_code']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Contact Info', {'fields': ('phone_number',)}),
        ('OTP Details', {'fields': ('otp_code', 'otp_type', 'is_verified')}),
        ('Rate Limiting', {'fields': ('attempts', 'blocked_until')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role_name', 'shop', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'shop']
    search_fields = ['role_name', 'shop__shop_name']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Role Info', {'fields': ('role_name', 'shop')}),
        ('Permissions', {'fields': ('permissions',)}),
        ('Status', {'fields': ('status',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(MenuMaster)
class MenuMasterAdmin(admin.ModelAdmin):
    list_display = ['id', 'menu_name', 'cust_menu_name', 'priority', 'menu_icon_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['menu_name', 'cust_menu_name', 'menu_icon_name']
    ordering = ['priority', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Menu Info', {'fields': ('menu_name', 'cust_menu_name', 'priority')}),
        ('Menu Details', {'fields': ('menu_icon_name', 'menu_url')}),
        ('Status', {'fields': ('status',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(MenuModuleMaster)
class MenuModuleMasterAdmin(admin.ModelAdmin):
    list_display = ['id', 'module_name', 'cust_module_name', 'menu', 'priority', 'module_visibility', 'status', 'created_at']
    list_filter = ['status', 'module_visibility', 'menu', 'created_at']
    search_fields = ['module_name', 'cust_module_name', 'module_icon_name']
    ordering = ['priority', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Module Info', {'fields': ('menu', 'module_name', 'cust_module_name', 'priority')}),
        ('Module Details', {'fields': ('module_url', 'module_description', 'module_permission_type_ids', 'module_icon_name')}),
        ('Visibility & Status', {'fields': ('module_visibility', 'status')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
