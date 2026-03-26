from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['id','phone_number', 'user_name', 'email', 'is_verified', 'is_active', 'is_staff', 'user_lock', 'status', 'created_at']
    list_filter = ['is_verified', 'is_active', 'is_staff', 'user_lock', 'status', 'created_at']
    search_fields = ['phone_number', 'email', 'user_name']
    ordering = ['-created_at']
    filter_horizontal = ['companies', 'branches', 'groups', 'user_permissions']

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Filter companies to only show companies owned by the current user (for company owners)
        if db_field.name == 'companies' and not request.user.is_superuser and request.user.is_staff and request.user.companies.exists():
            kwargs['queryset'] = request.user.companies.all()

        # Filter branches to only show branches owned by the current user (for company owners)
        if db_field.name == 'branches' and not request.user.is_superuser and request.user.is_staff and request.user.branches.exists():
            kwargs['queryset'] = request.user.branches.all()
        
        # Filter primary_company to only show companies owned by the current user (for company owners)
        if db_field.name == 'primary_company' and not request.user.is_superuser and request.user.is_staff and request.user.companies.exists():
            kwargs['queryset'] = request.user.companies.all()
        
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter primary_company foreign key to only show companies owned by the current user
        if db_field.name == 'primary_company' and not request.user.is_superuser and request.user.is_staff and request.user.companies.exists():
            kwargs['queryset'] = request.user.companies.all()

        # Filter primary_branch foreign key to only show branches owned by the current user
        if db_field.name == 'primary_branch' and not request.user.is_superuser and request.user.is_staff and request.user.branches.exists():
            kwargs['queryset'] = request.user.branches.all()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        # Superusers and company owners can add users
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())

    def has_view_permission(self, request, obj=None):
        # Superusers and company owners can view users
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())

    def has_module_permission(self, request):
        # Superusers and company owners can see the module
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusers see all users
        if request.user.is_superuser:
            return qs
        # Company owners only see users from their companies and themselves
        elif request.user.is_staff and request.user.companies.exists():
            return qs.filter(companies__in=request.user.companies.all()).distinct() | qs.filter(id=request.user.id).distinct()
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
        # Company owners can change users from their companies or themselves
        # For add views (obj=None), they need change permission to proceed
        if request.user.is_staff and request.user.companies.exists():
            if obj is None:
                # This is for the add view - allow company owners to proceed
                return True
            return obj.companies.filter(id__in=request.user.companies.all()).exists() or obj.id == request.user.id
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Superusers can delete everything
        if request.user.is_superuser:
            return True
        # Company owners can only delete users from their companies (not themselves)
        if request.user.is_staff and request.user.companies.exists() and obj:
            return obj.companies.filter(id__in=request.user.companies.all()).exists() and obj.id != request.user.id
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # If company owner is creating/updating user, restrict companies to their own companies
        if not request.user.is_superuser and request.user.is_staff and request.user.companies.exists():
            # Only allow assigning to companies that the current user owns
            if hasattr(obj, 'companies'):
                obj.companies.set(request.user.companies.all())
            # Set primary_company to one of the company owner's companies
            if hasattr(obj, 'primary_company') and obj.primary_company:
                if obj.primary_company not in request.user.companies.all():
                    obj.primary_company = request.user.companies.first()

            # Only allow assigning to branches that the current user owns
            if hasattr(obj, 'branches') and request.user.branches.exists():
                obj.branches.set(request.user.branches.all())
            # Set primary_branch to one of the company owner's branches
            if hasattr(obj, 'primary_branch') and obj.primary_branch:
                if obj.primary_branch not in request.user.branches.all():
                    obj.primary_branch = request.user.branches.first()
        
        super().save_model(request, obj, form, change)

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('id','email', 'user_name')}),
        ('Address Info', {'fields': ('address', 'country', 'state', 'city', 'pincode')}),
        ('Company Info', {'fields': ('companies', 'primary_company', 'branches', 'primary_branch')}),
        ('Permissions', {'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser', 'user_lock', 'status', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'email', 'user_name', 'is_verified', 'companies', 'primary_company', 'branches', 'primary_branch', 'address', 'country', 'state', 'city', 'pincode', 'profile_image', 'is_active', 'user_lock', 'status'),
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
