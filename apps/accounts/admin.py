from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['id','phone_number', 'user_name', 'email', 'is_verified', 'is_active', 'is_staff', 'user_lock', 'status', 'created_at']
    list_filter = ['is_verified', 'is_active', 'is_staff', 'user_lock', 'status', 'created_at']
    search_fields = ['phone_number', 'email', 'user_name']
    ordering = ['-created_at']
    filter_horizontal = ['groups', 'user_permissions']

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        # Superusers and company owners can add users
        return request.user.is_superuser or (request.user.is_staff and request.user.company)

    def has_view_permission(self, request, obj=None):
        # Superusers and company owners can view users
        return request.user.is_superuser or (request.user.is_staff and request.user.company)

    def has_module_permission(self, request):
        # Superusers and company owners can see the module
        return request.user.is_superuser or (request.user.is_staff and request.user.company)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusers see all users
        if request.user.is_superuser:
            return qs
        # Company owners only see users from their company and themselves
        elif request.user.is_staff and request.user.company:
            return qs.filter(company=request.user.company) | qs.filter(id=request.user.id).distinct()
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
        # Only superusers have restrictions - company owners get full access
        if not request.user.is_superuser and not request.user.is_staff:
            readonly_fields.extend(['is_staff', 'is_superuser', 'is_active', 'user_lock'])
        return readonly_fields

    def has_change_permission(self, request, obj=None):
        # Superusers can change everything
        if request.user.is_superuser:
            return True
        # Company owners can change users from their company or themselves
        # For add views (obj=None), they need change permission to proceed
        if request.user.is_staff and request.user.company:
            if obj is None:
                # This is for the add view - allow company owners to proceed
                return True
            return obj.company == request.user.company or obj.id == request.user.id
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Superusers can delete everything
        if request.user.is_superuser:
            return True
        # Company owners can only delete users from their company (not themselves)
        if request.user.is_staff and request.user.company and obj:
            return obj.company == request.user.company and obj.id != request.user.id
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('id','email', 'user_name')}),
        ('Address Info', {'fields': ('address', 'country', 'state', 'city', 'pincode')}),
        ('Company Info', {'fields': ('company', 'branch', 'branch_access')}),
        ('Permissions', {'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser', 'user_lock', 'status', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'email', 'user_name', 'is_verified', 'company', 'branch', 'branch_access', 'address', 'country', 'state', 'city', 'pincode', 'profile_image', 'is_active', 'user_lock', 'status'),
        }),
    )

    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']


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
