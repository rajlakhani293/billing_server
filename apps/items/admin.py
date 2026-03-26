from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django import forms
from django.utils.safestring import mark_safe
from django.db import models
from .models import Item, ItemCategory, ItemUnit, StockLedger

@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ["id", 'item_code', 'item_name', 'category', 'primary_unit', 'current_stock', 'status', 'company', 'branch']
    list_filter = ['category', 'primary_unit', 'status', 'company', 'branch', 'brand']
    search_fields = ['item_code', 'item_name', 'brand', 'barcode']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('item_code', 'item_name', 'category', 'item_images', 'description', 'company', 'branch')
        }),
        ('Pricing Information', {
            'fields': ('purchase_price', 'selling_price')
        }),
        ('Inventory Management', {
            'fields': ('opening_stock', 'current_stock', 'min_stock_level')
        }),
        ('Units and Measurements', {
            'fields': ('primary_unit', 'item_weight')
        }),
        ('Additional Details', {
            'fields': ('brand', 'barcode')
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
    

@admin.register(ItemCategory)
class ItemCategoryAdmin(ModelAdmin):
    list_display = ["id", 'category_name', 'company', 'branch', 'status']
    list_filter = ['status', 'company', 'branch']
    search_fields = ['category_name', 'description']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category_name', 'description', 'company', 'branch')
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


@admin.register(ItemUnit)
class ItemUnitAdmin(ModelAdmin):
    list_display = ["id", 'unit_name', 'short_name', 'company', 'branch', 'status']
    list_filter = ['status', 'company', 'branch']
    search_fields = ['unit_name', 'short_name']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('unit_name', 'short_name', 'company', 'branch')
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


@admin.register(StockLedger)
class StockLedgerAdmin(ModelAdmin):
    list_display = ["id", "item", "movement_type", "direction", "quantity", "balance_after", "company", "branch", "created_at"]
    list_filter = ["movement_type", "direction", "company", "branch", "status"]
    search_fields = ["item__item_name", "reference_type", "note"]
    readonly_fields = [field.name for field in StockLedger._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
