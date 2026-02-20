from django.db import models
from apps.core.models import IntegerModel, TimestampedModel
from apps.shops.models import Shop

class ItemCategory(IntegerModel, TimestampedModel):
    category_name = models.CharField(max_length=150, blank=False, null=False, help_text='Category name')
    description = models.TextField(blank=True, null=True, help_text='Category description')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='item_categories', help_text='Associated shop')

    class Meta:
        db_table = 'item_categories'
        verbose_name = 'Item Category'
        verbose_name_plural = 'Item Categories'
        ordering = ['category_name']
        indexes = [
            models.Index(fields=['shop', 'category_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'category_name']]
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
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='item_units', help_text='Associated shop')

    class Meta:
        db_table = 'item_units'
        verbose_name = 'Item Unit'
        verbose_name_plural = 'Item Units'
        ordering = ['unit_name']
        indexes = [
            models.Index(fields=['shop', 'unit_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'unit_name']]

    def __str__(self):
        return f"{self.unit_name} ({self.short_name})"


class Brand(IntegerModel, TimestampedModel):
    brand_name = models.CharField(max_length=150, blank=False, null=False, help_text='Brand name')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='brands', help_text='Associated shop')

    class Meta:
        db_table = 'brands'
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        ordering = ['brand_name']
        indexes = [
            models.Index(fields=['shop', 'brand_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'brand_name']]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(brand_name=""), 
                name="brand_name_not_empty"
            )
        ]

    def __str__(self):
        return self.brand_name


class Tax(IntegerModel, TimestampedModel):
    tax_name = models.CharField(max_length=150, unique=True, blank=False, null=False, help_text='Tax name')
    tax_value = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Tax value/percentage')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='taxes', help_text='Associated shop')

    class Meta:
        db_table = 'taxes'
        verbose_name = 'Tax'
        verbose_name_plural = 'Taxes'
        ordering = ['tax_name']
        indexes = [
            models.Index(fields=['shop', 'tax_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'tax_name']]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(tax_name=""), 
                name="tax_name_not_empty"
            ),
            models.CheckConstraint(
                check=models.Q(tax_value__gte=0), 
                name="tax_value_non_negative"
            )
        ]

    def __str__(self):
        return f"{self.tax_name} ({self.tax_value}%)"


class Item(IntegerModel, TimestampedModel):
    
    # Basic Information
    item_code = models.CharField(max_length=50, blank=False, null=False, help_text='Unique item code/SKU')
    item_image = models.ImageField(upload_to='item_image', blank=True, null=True, help_text='Item image')
    item_name = models.CharField(max_length=255, blank=False, null=False, help_text='Item name')
    category = models.ForeignKey(ItemCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', help_text='Item category')
    description = models.TextField(blank=True, null=True, help_text='Item description')
    
    # Pricing
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Purchase price')
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Selling price')
    
    # Tax Information
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', help_text='Tax rate')
    hsn_code = models.CharField(max_length=20, blank=True, null=True, help_text='HSN/SAC code')
    
    # Inventory
    opening_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Opening stock')
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Current stock')
    min_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Minimum stock level')
    max_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Maximum stock level')
    
    # Units and Measurements
    primary_unit = models.ForeignKey(ItemUnit, on_delete=models.SET_NULL, null=True, related_name='items_primary', blank=False, help_text='Primary unit of measurement')
    item_weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text='Weight per unit')
    
    # Additional Details
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', help_text='Brand name')
    barcode = models.CharField(max_length=50, blank=True, null=True, help_text='Barcode', unique=True)
    
    # Status and Shop
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='items', help_text='Associated shop')
    
    class Meta:
        db_table = 'items'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['item_name']
        unique_together = [
            ['shop', 'item_code'], 
            ['shop', 'item_name'], 
            ['shop', 'barcode']    
        ]
        indexes = [
            models.Index(fields=['shop', 'item_code']),
            models.Index(fields=['shop', 'item_name']),
            models.Index(fields=['status']),
            models.Index(fields=['brand']),
            models.Index(fields=['tax']),
        ]
    
    def __str__(self):
        return f"{self.item_name} ({self.item_code})"
