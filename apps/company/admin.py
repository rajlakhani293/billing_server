from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import Company, Branch


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['id','company_code', 'company_name', 'phone_number', 'email', 'owner', 'default_company', 'status', 'created_at']
    list_filter = ['default_company', 'status', 'created_at']
    search_fields = ['company_code', 'company_name', 'phone_number', 'email', 'pan_no']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def has_add_permission(self, request):
        # Superusers and company owners can add companies
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())

    def has_view_permission(self, request, obj=None):
        # Superusers and company owners can view companies
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())

    def has_module_permission(self, request):
        # Superusers and company owners can see the module
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusers see all companies
        if request.user.is_superuser:
            return qs
        # Company owners only see their own companies
        elif request.user.is_staff and request.user.companies.exists():
            return qs.filter(id__in=request.user.companies.all())
        return qs.none()

    def has_change_permission(self, request, obj=None):
        # Superusers can change everything
        if request.user.is_superuser:
            return True
        # Company owners can only edit their own companies
        if request.user.is_staff and request.user.companies.exists() and obj:
            return obj.id in [company.id for company in request.user.companies.all()]
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Superusers can delete everything
        if request.user.is_superuser:
            return True
        # Company owners can only delete their own companies (but not their primary company)
        if request.user.is_staff and request.user.companies.exists() and obj:
            return obj.id in [company.id for company in request.user.companies.all()] and obj.id != request.user.primary_company.id
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # When creating a new company, set default password for the company owner if provided
        if not change and obj.email and not obj.password:
            # Set default password "admin123" for new company owners
            obj.password = make_password('admin123')
            messages.success(request, f'Default password "admin123" has been set for company owner: {obj.email}')
        
        super().save_model(request, obj, form, change)

    fieldsets = (
        ('Basic Info', {'fields': ('id','company_code', 'company_name', 'owner')}),
        ('Contact Info', {'fields': ('phone_number', 'email')}),
        ('Tax Info', {'fields': ('pan_no',)}),
        ('Address Info', {'fields': ('address', 'pincode', 'country', 'state', 'city')}),
        ('Settings', {'fields': ('default_company', 'status', 'logo_image')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['id', 'branch_name', 'company', 'phone_number', 'email', 'status', 'created_at']
    list_filter = ['status', 'company', 'created_at']
    search_fields = ['branch_name', 'phone_number', 'email']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def has_add_permission(self, request):
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())

    def has_module_permission(self, request):
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('company')
        if request.user.is_superuser:
            return qs
        if request.user.is_staff and request.user.companies.exists():
            return qs.filter(company__in=request.user.companies.all())
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and hasattr(request.user, 'companies'):
            form.base_fields['company'].queryset = request.user.companies.all()
        return form

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_staff and request.user.companies.exists() and obj:
            return obj.company.id in [company.id for company in request.user.companies.all()]
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_staff and request.user.companies.exists() and obj:
            return obj.company.id in [company.id for company in request.user.companies.all()]
        return super().has_delete_permission(request, obj)

    fieldsets = (
        ('Basic Info', {'fields': ('id', 'branch_name', 'company')}),
        ('Contact Info', {'fields': ('phone_number', 'email')}),
        ('Address Info', {'fields': ('address', 'pincode', 'country', 'state', 'city')}),
        ('Settings', {'fields': ('status',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
