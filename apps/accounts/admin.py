from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, MenuMaster, MenuModuleMaster


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['id','phone_number', 'user_name', 'email', 'is_verified', 'is_active', 'is_staff', 'user_lock', 'status', 'created_at']
    list_filter = ['is_verified', 'is_active', 'is_staff', 'user_lock', 'status', 'created_at']
    search_fields = ['phone_number', 'email', 'user_name']
    ordering = ['-created_at']
    filter_horizontal = ['shops', 'groups', 'user_permissions']

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Filter shops to only show shops owned by the current user (for shop owners)
        if db_field.name == 'shops' and not request.user.is_superuser and request.user.is_staff and request.user.shops.exists():
            kwargs['queryset'] = request.user.shops.all()
        
        # Filter primary_shop to only show shops owned by the current user (for shop owners)
        if db_field.name == 'primary_shop' and not request.user.is_superuser and request.user.is_staff and request.user.shops.exists():
            kwargs['queryset'] = request.user.shops.all()
        
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter primary_shop foreign key to only show shops owned by the current user
        if db_field.name == 'primary_shop' and not request.user.is_superuser and request.user.is_staff and request.user.shops.exists():
            kwargs['queryset'] = request.user.shops.all()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        # Superusers and shop owners can add users
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())

    def has_view_permission(self, request, obj=None):
        # Superusers and shop owners can view users
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())

    def has_module_permission(self, request):
        # Superusers and shop owners can see the module
        return request.user.is_superuser or (request.user.is_staff and request.user.shops.exists())

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusers see all users
        if request.user.is_superuser:
            return qs
        # Shop owners only see users from their shops and themselves
        elif request.user.is_staff and request.user.shops.exists():
            return qs.filter(shops__in=request.user.shops.all()).distinct() | qs.filter(id=request.user.id).distinct()
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
        # Only superusers have restrictions - shop owners get full access
        if not request.user.is_superuser and not request.user.is_staff:
            readonly_fields.extend(['is_staff', 'is_superuser', 'is_active', 'user_lock'])
        return readonly_fields

    def has_change_permission(self, request, obj=None):
        # Superusers can change everything
        if request.user.is_superuser:
            return True
        # Shop owners can change users from their shops or themselves
        # For add views (obj=None), they need change permission to proceed
        if request.user.is_staff and request.user.shops.exists():
            if obj is None:
                # This is for the add view - allow shop owners to proceed
                return True
            return obj.shops.filter(id__in=request.user.shops.all()).exists() or obj.id == request.user.id
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Superusers can delete everything
        if request.user.is_superuser:
            return True
        # Shop owners can only delete users from their shops (not themselves)
        if request.user.is_staff and request.user.shops.exists() and obj:
            return obj.shops.filter(id__in=request.user.shops.all()).exists() and obj.id != request.user.id
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # If shop owner is creating/updating user, restrict shops to their own shops
        if not request.user.is_superuser and request.user.is_staff and request.user.shops.exists():
            # Only allow assigning to shops that the current user owns
            if hasattr(obj, 'shops'):
                obj.shops.set(request.user.shops.all())
            # Set primary_shop to one of the shop owner's shops
            if hasattr(obj, 'primary_shop') and obj.primary_shop:
                if obj.primary_shop not in request.user.shops.all():
                    obj.primary_shop = request.user.shops.first()
        
        super().save_model(request, obj, form, change)

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('id','email', 'user_name')}),
        ('Address Info', {'fields': ('address', 'country', 'state', 'city', 'pincode')}),
        ('Shop Info', {'fields': ('shops', 'primary_shop')}),
        ('Permissions', {'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser', 'user_lock', 'status', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'email', 'user_name', 'is_verified', 'shops', 'primary_shop', 'address', 'country', 'state', 'city', 'pincode', 'profile_image', 'is_active', 'user_lock', 'status'),
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

@admin.register(MenuMaster)
class MenuMasterAdmin(admin.ModelAdmin):
    list_display = ['id', 'menu_name', 'cust_menu_name', 'priority', 'menu_icon_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['menu_name', 'cust_menu_name', 'menu_icon_name']
    ordering = ['priority', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def has_view_permission(self, request, obj=None):
        # Only superusers can view menus
        return request.user.is_superuser

    def has_module_permission(self, request):
        # Only superusers can see the menu module
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only superusers see all menus
        if request.user.is_superuser:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        # Only superusers can change menus
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete menus
        return request.user.is_superuser
    
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
    
    def has_view_permission(self, request, obj=None):
        # Only superusers can view modules
        return request.user.is_superuser

    def has_module_permission(self, request):
        # Only superusers can see the module module
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only superusers see all modules
        if request.user.is_superuser:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        # Only superusers can change modules
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete modules
        return request.user.is_superuser
    
    fieldsets = (
        ('Module Info', {'fields': ('menu', 'module_name', 'cust_module_name', 'priority')}),
        ('Module Details', {'fields': ('module_url', 'module_description', 'module_permission_type_ids', 'module_icon_name')}),
        ('Visibility & Status', {'fields': ('module_visibility', 'status')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
