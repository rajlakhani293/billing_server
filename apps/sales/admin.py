from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Sales, SalesTransaction
from apps.settings.models import Party


class SalesTransactionInline(TabularInline):
    model = SalesTransaction
    extra = 1
    readonly_fields = ['tax_amount', 'discount_amount']
    fields = ['item', 'item_quantity', 'item_rate', 'discount_percentage']


@admin.register(Sales)
class SalesAdmin(ModelAdmin):
    list_display = ["id", 'sales_code', 'party', 'company', 'branch', 'total_amount', 'paid_amount', 'payment_mode', 'status']
    list_filter = ['payment_mode', 'company', 'branch', 'party']
    search_fields = ['sales_code', 'party__name', 'notes']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SalesTransactionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('sales_code', 'party', 'company', 'branch')
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
        return request.user.is_superuser or (request.user.is_staff and request.user.companies.exists())
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('party', 'company')
        
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
            form.base_fields['party'].queryset = Party.objects.filter(company__in=request.user.companies.all())
        if not request.user.is_superuser and hasattr(request.user, 'branches') and 'branch' in form.base_fields:
            form.base_fields['branch'].queryset = request.user.branches.all()
            form.base_fields['party'].queryset = Party.objects.filter(branch__in=request.user.branches.all())
        
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
