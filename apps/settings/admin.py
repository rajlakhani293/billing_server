from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Brand, Tax, Party


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ["id", 'brand_name', 'company', 'branch', 'status']
    list_filter = ['status', 'company', 'branch']
    search_fields = ['brand_name']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('brand_name', 'company', 'branch')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def has_module_permission(self, request):
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('company')
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return qs.filter(branch__in=user_branch_ids)
        if hasattr(request.user, 'companies') and request.user.companies.exists():
            user_company_ids = request.user.companies.values_list('id', flat=True)
            return qs.filter(company__in=user_company_ids)
        
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser and hasattr(request.user, 'companies'):
            form.base_fields['company'].queryset = request.user.companies.all()
        if not request.user.is_superuser and hasattr(request.user, 'branches') and 'branch' in form.base_fields:
            form.base_fields['branch'].queryset = request.user.branches.all()
        
        return form
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'companies') and request.user.companies.exists()
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return obj.branch_id in user_branch_ids
        user_company_ids = request.user.companies.values_list('id', flat=True)
        return obj.company_id in user_company_ids
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'companies') and request.user.companies.exists()
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return obj.branch_id in user_branch_ids
        user_company_ids = request.user.companies.values_list('id', flat=True)
        return obj.company_id in user_company_ids
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'companies') and request.user.companies.exists()
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return obj.branch_id in user_branch_ids
        user_company_ids = request.user.companies.values_list('id', flat=True)
        return obj.company_id in user_company_ids
    
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'companies') and request.user.companies.exists()


@admin.register(Tax)
class TaxAdmin(ModelAdmin):
    list_display = ["id", 'tax_name', 'tax_value', 'company', 'branch', 'status']
    list_filter = ['status', 'company', 'branch']
    search_fields = ['tax_name']
    list_editable = ['status', 'tax_value']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tax_name', 'tax_value', 'company', 'branch')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def has_module_permission(self, request):
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('company')
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return qs.filter(branch__in=user_branch_ids)
        if hasattr(request.user, 'companies') and request.user.companies.exists():
            user_company_ids = request.user.companies.values_list('id', flat=True)
            return qs.filter(company__in=user_company_ids)
        
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser and hasattr(request.user, 'companies'):
            form.base_fields['company'].queryset = request.user.companies.all()
        if not request.user.is_superuser and hasattr(request.user, 'branches') and 'branch' in form.base_fields:
            form.base_fields['branch'].queryset = request.user.branches.all()
        
        return form
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'companies') and request.user.companies.exists()
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return obj.branch_id in user_branch_ids
        user_company_ids = request.user.companies.values_list('id', flat=True)
        return obj.company_id in user_company_ids
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'companies') and request.user.companies.exists()
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return obj.branch_id in user_branch_ids
        user_company_ids = request.user.companies.values_list('id', flat=True)
        return obj.company_id in user_company_ids
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'companies') and request.user.companies.exists()
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return obj.branch_id in user_branch_ids
        user_company_ids = request.user.companies.values_list('id', flat=True)
        return obj.company_id in user_company_ids
    
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'companies') and request.user.companies.exists()


@admin.register(Party)
class PartyAdmin(ModelAdmin):
    list_display = ["id", 'name', 'party_type', 'phone_number', 'company', 'branch', 'status']
    list_filter = ['party_type', 'status', 'company', 'branch']
    search_fields = ['name', 'phone_number', 'email']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'party_type', 'phone_number', 'email', 'company', 'branch')
        }),
        ('Address Details', {
            'fields': ('address', 'city', 'state', 'country', 'pincode')
        }),
        ('Financial Info', {
            'fields': ('balance_type', 'customer_category')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def has_module_permission(self, request):
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('company', 'city', 'state', 'country')
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return qs.filter(branch__in=user_branch_ids)
        if hasattr(request.user, 'companies') and request.user.companies.exists():
            user_company_ids = request.user.companies.values_list('id', flat=True)
            return qs.filter(company__in=user_company_ids)
        
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser and hasattr(request.user, 'companies'):
            form.base_fields['company'].queryset = request.user.companies.all()
        if not request.user.is_superuser and hasattr(request.user, 'branches') and 'branch' in form.base_fields:
            form.base_fields['branch'].queryset = request.user.branches.all()
        
        return form
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'companies') and request.user.companies.exists()
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return obj.branch_id in user_branch_ids
        user_company_ids = request.user.companies.values_list('id', flat=True)
        return obj.company_id in user_company_ids
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'companies') and request.user.companies.exists()
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return obj.branch_id in user_branch_ids
        user_company_ids = request.user.companies.values_list('id', flat=True)
        return obj.company_id in user_company_ids
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return hasattr(request.user, 'companies') and request.user.companies.exists()
        if hasattr(request.user, 'branches') and request.user.branches.exists():
            user_branch_ids = request.user.branches.values_list('id', flat=True)
            return obj.branch_id in user_branch_ids
        user_company_ids = request.user.companies.values_list('id', flat=True)
        return obj.company_id in user_company_ids
    
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'companies') and request.user.companies.exists()
