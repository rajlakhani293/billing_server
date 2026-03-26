from django.db import models
from apps.core.models import IntegerModel, TimestampedModel
from apps.company.models import Company, Branch
from apps.settings.models import Brand

class ItemCategory(IntegerModel, TimestampedModel):
    category_name = models.CharField(max_length=150, blank=False, null=False, help_text='Category name')
    description = models.TextField(blank=True, null=True, help_text='Category description')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='item_categories', help_text='Associated company')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='item_categories', null=True, blank=True, help_text='Associated branch')

    class Meta:
        db_table = 'item_categories'
        verbose_name = 'Item Category'
        verbose_name_plural = 'Item Categories'
        ordering = ['category_name']
        indexes = [
            models.Index(fields=['company', 'branch', 'category_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['company', 'branch', 'category_name']]
        constraints = [
        models.CheckConstraint(
            check=~models.Q(category_name=""), 
            name="category_name_not_empty"
        )
    ]

    def __str__(self):
        return self.category_name


class ItemUnit(IntegerModel, TimestampedModel):
    unit_name = models.CharField(max_length=100, blank=False, null=False, help_text='Unit name (e.g., Kilogram)')
    short_name = models.CharField(max_length=50, help_text='Short name (e.g., kg)')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='item_units', help_text='Associated company')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='item_units', null=True, blank=True, help_text='Associated branch')

    class Meta:
        db_table = 'item_units'
        verbose_name = 'Item Unit'
        verbose_name_plural = 'Item Units'
        ordering = ['unit_name']
        indexes = [
            models.Index(fields=['company', 'branch', 'unit_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['company', 'branch', 'unit_name']]

    def __str__(self):
        return f"{self.unit_name} ({self.short_name})"


class Item(IntegerModel, TimestampedModel):
    
    # Basic Information
    item_code = models.CharField(max_length=50, blank=False, null=False, help_text='Unique item code/SKU')
    item_images = models.JSONField(default=list, blank=True, help_text='List of images with metadata (url, sort_order, is_primary)')
    item_name = models.CharField(max_length=255, blank=False, null=False, help_text='Item name')
    category = models.ForeignKey(ItemCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', help_text='Item category')
    description = models.TextField(blank=True, null=True, help_text='Item description')
    
    # Pricing
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text='Purchase price')
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, help_text='Selling price')
        
    # Inventory
    opening_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Opening stock')
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Current stock')
    min_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Minimum stock level')
    
    # Units and Measurements
    primary_unit = models.ForeignKey(ItemUnit, on_delete=models.SET_NULL, null=True, related_name='items_primary', blank=False, help_text='Primary unit of measurement')
    item_weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text='Weight per unit')
    
    # Additional Details
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='brand', help_text='Brand name')
    barcode = models.CharField(max_length=50, blank=True, null=True, help_text='Barcode', unique=True)
    
    # Status and Company
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='items', help_text='Associated company')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='items', null=True, blank=True, help_text='Associated branch')
    
    class Meta:
        db_table = 'items'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['item_name']
        unique_together = [
            ['company', 'branch', 'item_code'], 
            ['company', 'branch', 'item_name'], 
            ['company', 'branch', 'barcode']    
        ]
        indexes = [
            models.Index(fields=['company', 'branch', 'item_code']),
            models.Index(fields=['company', 'branch', 'item_name']),
            models.Index(fields=['status']),
            models.Index(fields=['company', 'branch', 'brand']),
        ]
    
    def __str__(self):
        return f"{self.item_name} ({self.item_code})"


class StockLedger(IntegerModel, TimestampedModel):
    MOVEMENT_TYPES = [
        ("OPENING_STOCK", "Opening Stock"),
        ("PURCHASE", "Purchase"),
        ("SALES_RETURN", "Sales Return"),
        ("TRANSFER_IN", "Transfer In"),
        ("ADJUSTMENT_IN", "Adjustment In"),
        ("SALE", "Sale"),
        ("PURCHASE_RETURN", "Purchase Return"),
        ("TRANSFER_OUT", "Transfer Out"),
        ("DAMAGE", "Damage"),
        ("ADJUSTMENT_OUT", "Adjustment Out"),
        ("SAMPLE_GIVEN", "Sample Given"),
        ("INTERNAL_USE", "Internal Use"),
        ("THEFT_LOSS", "Theft / Loss"),
        ("DAMAGE_EXPIRED", "Damage / Expired"),
    ]

    DIRECTION_CHOICES = [
        ("IN", "In"),
        ("OUT", "Out"),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="stock_ledger_entries")
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, help_text="Moved quantity")
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, help_text="Stock after movement")
    reference_type = models.CharField(max_length=50, blank=True, null=True, help_text="Source document type")
    reference_id = models.IntegerField(blank=True, null=True, help_text="Source document ID")
    note = models.TextField(blank=True, null=True)
    status = models.IntegerField(default=0, help_text="0: Active, 1: Inactive, 2: Deleted")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="stock_ledger_entries")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="stock_ledger_entries", null=True, blank=True)

    class Meta:
        db_table = "stock_ledger"
        verbose_name = "Stock Ledger"
        verbose_name_plural = "Stock Ledger"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "branch", "item", "created_at"]),
            models.Index(fields=["movement_type", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.item.item_name} - {self.movement_type} ({self.quantity})"
